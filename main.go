package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/BurntSushi/toml"
)

type Link struct {
	Source string `toml:"source"`
	Dest   string `toml:"dest"`
}

type Module struct {
	Packages []string `toml:"packages"`
	Links    []Link   `toml:"links"`
}

type Profile struct {
	ModuleNames    []string `toml:"modules"`
	PackageManager string   `toml:"package_manager"`
}

type Config struct {
	Modules  map[string]Module  `toml:"modules"`
	Profiles map[string]Profile `toml:"profiles"`
}

func profileLinks(name string, config Config) ([]Link, error) {
	profile, ok := config.Profiles[name]
	if ok == false {
		return nil, fmt.Errorf("unknown profile %q", name)
	}

	links := []Link{}
	for _, moduleName := range profile.ModuleNames {
		module, ok := config.Modules[moduleName]
		if ok == false {
			return nil, fmt.Errorf("unknown module %q", moduleName)
		}

		for _, link := range module.Links {
			links = append(links, link)
		}
	}
	return links, nil
}

func absolutePath(path string) (string, error) {
	rest, found := strings.CutPrefix(path, "~/")
	if found == false {
		return path, nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(home, rest), nil
}

func main() {
	fmt.Printf("Hello from dot\n")

	config := Config{}
	_, err := toml.DecodeFile("examples/dotfiles.toml", &config)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	ubuntuLinks, err := profileLinks("ubuntu", config)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	for _, link := range ubuntuLinks {
		path, err := absolutePath(link.Dest)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		fmt.Printf("Dest: %q\n", path)
	}
}

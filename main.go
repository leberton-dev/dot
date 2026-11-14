package main

import (
	"errors"
	"fmt"
	"io/fs"
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

func destPath(path string) (string, error) {
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

func sourcePath(configPath string, path string) (string, error) {
	absConfig, err := filepath.Abs(configPath)
	if err != nil {
		return "", err
	}
	configDir := filepath.Dir(absConfig)
	return filepath.Join(configDir, path), nil
}

func linkStatus(link Link, configPath string) (string, error) {
	dest, err := destPath(link.Dest)
	if err != nil {
		return "", err
	}
	info, err := os.Lstat(dest)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return "missing", nil
		}
		return "", err
	}

	if info.Mode()&os.ModeSymlink != 0 {
		source, err := sourcePath(configPath, link.Source)
		if err != nil {
			return "", err
		}
		destLink, err := os.Readlink(dest)
		if err != nil {
			return "", err
		}
		if destLink == source {
			return "is linked", nil
		}
		return "linked improperly", nil
	}
	return "real file", nil
}

func main() {
	fmt.Printf("Hello from dot\n")

	// tomlPath := "/home/theleberton/.dotfiles/dotfiles.toml"
	tomlPath := "examples/dotfiles.toml"

	config := Config{}
	_, err := toml.DecodeFile(tomlPath, &config)
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
		status, err := linkStatus(link, tomlPath)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		fmt.Printf("%-30s -> %s\n", link.Source, status)
	}
}

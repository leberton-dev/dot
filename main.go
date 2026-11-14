package main

import (
	"fmt"
	"os"

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

func profileLinks(name string, config Config) []Link {
	links := []Link{}
	for _, moduleName := range config.Profiles[name].ModuleNames {
		for _, link := range config.Modules[moduleName].Links {
			links = append(links, link)
		}
	}
	return links
}

func main() {
	fmt.Printf("Hello from dot\n")

	config := Config{}
	_, err := toml.DecodeFile("examples/dotfiles.toml", &config)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	ubuntuLinks := profileLinks("ubuntu", config)
	fmt.Println(ubuntuLinks)
}

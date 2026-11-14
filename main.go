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

func main() {
	fmt.Println("Hello from dot\n")

	config := Config{}
	_, err := toml.DecodeFile("examples/dotfiles.toml", &config)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	for name, profile := range config.Profiles {
		fmt.Println(name, profile.ModuleNames)
	}
	fmt.Println("\n")

	for name, module := range config.Modules {
		fmt.Println(name, module)
	}
}

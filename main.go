package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Printf("Hello from dot\n")

	// tomlPath := "/home/theleberton/.dotfiles/dotfiles.toml"
	tomlPath := "examples/dotfiles.toml"

	config, err := loadConfig(tomlPath)
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

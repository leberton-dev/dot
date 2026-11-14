package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	fmt.Printf("Hello from dot\n")

	configPath := flag.String("config", "~/.dotfiles/dotfiles.toml", "config path")
	profile := flag.String("profile", "ubuntu", "profile to use")
	flag.Parse()

	tomlPath, err := expandHome(*configPath)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	config, err := loadConfig(tomlPath)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	links, err := profileLinks(*profile, config)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	for _, link := range links {
		status, err := linkStatus(link, tomlPath)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		fmt.Printf("%-30s -> %s\n", link.Source, status)
	}
}

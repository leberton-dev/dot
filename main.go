package main

import (
	"flag"
	"fmt"
	"os"
)

func runStatus(profile string, config Config, configPath string) {
	links, err := profileLinks(profile, config)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	for _, link := range links {
		status, err := linkStatus(link, configPath)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		fmt.Printf("%-30s -> %s\n", link.Source, status)
	}

}

func main() {
	if len(os.Args) == 1 {
		fmt.Fprintln(os.Stderr, "usage: dot <command> [--config PATH] [--profile NAME]")
		fmt.Fprintln(os.Stderr, "commands: status")
		os.Exit(2)
	}
	command := os.Args[1]

	flags := flag.NewFlagSet(command, flag.ExitOnError)
	configPath := flags.String("config", "~/.dotfiles/dotfiles.toml", "config path")
	profile := flags.String("profile", "ubuntu", "profile to use")
	flags.Parse(os.Args[2:])

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

	switch command {
	case "status":
		runStatus(*profile, config, tomlPath)
	default:
		fmt.Fprintf(os.Stderr, "dot: unknown command %q\n", command)
		fmt.Fprintln(os.Stderr, "run 'dot' without arguments to see usage")
		os.Exit(2)
	}
}

package main

import (
	"flag"
	"fmt"
	"io"
	"os"
)

func main() {
	if len(os.Args) == 1 {
		fmt.Fprintln(os.Stderr, "usage: dot <command> [--config PATH] [--profile NAME]")
		fmt.Fprintln(os.Stderr, "commands: status, install")
		os.Exit(2)
	}
	command := os.Args[1]

	flags := flag.NewFlagSet(command, flag.ContinueOnError)
	flags.SetOutput(io.Discard)
	configPath := flags.String("config", "~/.dotfiles/dotfiles.toml", "config path")
	profile := flags.String("profile", "ubuntu", "profile to use")
	err := flags.Parse(os.Args[2:])
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		fmt.Fprintln(os.Stderr, "run 'dot' without arguments to see usage")
		os.Exit(2)
	}

	tomlPath, err := expandHome(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}

	config, err := loadConfig(tomlPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}

	switch command {
	case "status":
		runStatus(*profile, config, tomlPath)
	case "install":
		runInstall(*profile, config, tomlPath)
	default:
		fmt.Fprintf(os.Stderr, "dot: unknown command %q\n", command)
		fmt.Fprintln(os.Stderr, "run 'dot' without arguments to see usage")
		os.Exit(2)
	}
}

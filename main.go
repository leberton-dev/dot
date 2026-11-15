package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

func queryCommand(manager string) ([]string, error) {
	switch manager {
	case "apt":
		return []string{"dpkg", "-s"}, nil
	case "dnf":
		return []string{"rpm", "-q"}, nil
	case "brew":
		return []string{"brew", "list"}, nil
	}
	return []string{}, fmt.Errorf("unknown package manager %q", manager)
}

func runStatus(profile string, config Config, configPath string) {
	links, err := profileLinks(profile, config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}

	fmt.Println("Links:")
	for _, link := range links {
		status, err := linkStatus(link, configPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "dot: %s\n", err)
			os.Exit(1)
		}
		fmt.Printf("%-30s -> %s\n", link.Source, status)
	}
	fmt.Println()

	query, err := queryCommand(config.Profiles[profile].PackageManager)
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}

	packages, err := profilePackages(profile, config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}

	fmt.Println("Packages:")
	for _, pack := range packages {
		err := exec.Command(query[0], query[1], pack).Run()
		if err != nil {
			fmt.Printf("%-30s -> not installed\n", pack)
		} else {
			fmt.Printf("%-30s -> installed\n", pack)
		}
	}
}

func backupDir() (string, error) {
	state := os.Getenv("XDG_STATE_HOME")
	if state == "" {
		homeDir, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		state = filepath.Join(homeDir, ".local/state")
	}
	backDir := filepath.Join(state, "dot/backups")
	return backDir, nil
}

func installLink(link Link, configPath string, backDir string) error {
	status, err := linkStatus(link, configPath)
	if err != nil {
		return err
	}

	source, err := sourcePath(configPath, link.Source)
	if err != nil {
		return err
	}
	dest, err := expandHome(link.Dest)
	if err != nil {
		return err
	}

	switch status {
	case Unknown:
		return fmt.Errorf("unknown case %q", link.Dest)
	case Linked:
		fmt.Printf("%-30s -> nothing to do, already linked to %s\n", source, dest)
	case Missing:
		fmt.Printf("%-30s -> linking to %s\n", source, dest)
		err := os.Symlink(source, dest)
		if err != nil {
			return err
		}
	case WrongTarget, RealFile:
		backupPath := filepath.Join(backDir, dest)
		err := os.MkdirAll(filepath.Dir(backupPath), 0755)
		if err != nil {
			return err
		}
		err = os.Rename(dest, backupPath)
		if err != nil {
			return err
		}
		err = os.Symlink(source, dest)
		if err != nil {
			return err
		}
		fmt.Printf("%-30s -> backed up to %s and linked to %s\n", source, backupPath, dest)
	}
	return nil
}

func runInstall(profile string, config Config, configPath string) {
	links, err := profileLinks(profile, config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}

	backDir, err := backupDir()
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}
	backDir = filepath.Join(backDir, time.Now().Format("20060102_150405"))

	fmt.Println("Links:")
	for _, link := range links {
		err := installLink(link, configPath, backDir)
		if err != nil {
			fmt.Fprintf(os.Stderr, "dot: %s\n", err)
			os.Exit(1)
		}
	}
	fmt.Println()
}

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

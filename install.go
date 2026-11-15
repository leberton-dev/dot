package main

import (
	"fmt"
	"os"
	"path/filepath"
	"time"
)

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

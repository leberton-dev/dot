package main

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/BurntSushi/toml"
)

type InstallEntry struct {
	Dest   string `toml:"dest"`
	Backup string `toml:"backup"`
}

type InstallLog struct {
	Entries []InstallEntry `toml:"entries"`
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

func installLink(link Link, configPath string, backDir string) (InstallEntry, error) {
	status, err := linkStatus(link, configPath)
	if err != nil {
		return InstallEntry{}, err
	}

	source, err := sourcePath(configPath, link.Source)
	if err != nil {
		return InstallEntry{}, err
	}
	dest, err := expandHome(link.Dest)
	if err != nil {
		return InstallEntry{}, err
	}

	entry := InstallEntry{Dest: dest, Backup: ""}
	switch status {
	case Unknown:
		return InstallEntry{}, fmt.Errorf("unknown case %q", link.Dest)
	case Linked:
		fmt.Printf("%-30s -> nothing to do, already linked to %s\n", source, dest)
		entry.Dest = ""
	case Missing:
		fmt.Printf("%-30s -> linking to %s\n", source, dest)
		err := os.Symlink(source, dest)
		if err != nil {
			return InstallEntry{}, err
		}
	case WrongTarget, RealFile:
		backupPath := filepath.Join(backDir, dest)
		err := os.MkdirAll(filepath.Dir(backupPath), 0755)
		if err != nil {
			return InstallEntry{}, err
		}
		err = os.Rename(dest, backupPath)
		if err != nil {
			return InstallEntry{}, err
		}
		err = os.Symlink(source, dest)
		if err != nil {
			return InstallEntry{}, err
		}
		fmt.Printf("%-30s -> backed up to %s and linked to %s\n", source, backupPath, dest)
		entry.Backup = backupPath
	}
	return entry, nil
}

func writeInstallLog(backDir string, installLog InstallLog) error {
	err := os.MkdirAll(backDir, 0755)
	if err != nil {
		return err
	}

	file, err := os.Create(filepath.Join(backDir, "install_log.toml"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}
	defer file.Close()

	return toml.NewEncoder(file).Encode(installLog)
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

	installLog := InstallLog{}
	fmt.Println("Links:")
	for _, link := range links {
		entry, err := installLink(link, configPath, backDir)
		if err != nil {
			fmt.Fprintf(os.Stderr, "dot: %s\n", err)
			os.Exit(1)
		}
		if entry.Dest != "" {
			installLog.Entries = append(installLog.Entries, entry)
		}
	}
	fmt.Println()

	err = writeInstallLog(backDir, installLog)
	if err != nil {
		fmt.Fprintf(os.Stderr, "dot: %s\n", err)
		os.Exit(1)
	}
}

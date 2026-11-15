package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
)

type LinkStatus int

const (
	Unknown LinkStatus = iota
	Missing
	Linked
	WrongTarget
	RealFile
)

func (s LinkStatus) String() string {
	switch s {
	case Missing:
		return "missing"
	case Linked:
		return "linked"
	case WrongTarget:
		return "wrong target"
	case RealFile:
		return "real file"
	}
	return "unknown"
}

func linkStatus(link Link, configPath string) (LinkStatus, error) {
	dest, err := expandHome(link.Dest)
	if err != nil {
		return Unknown, err
	}
	info, err := os.Lstat(dest)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return Missing, nil
		}
		return Unknown, err
	}

	if info.Mode()&os.ModeSymlink != 0 {
		source, err := sourcePath(configPath, link.Source)
		if err != nil {
			return Unknown, err
		}
		destLink, err := os.Readlink(dest)
		if err != nil {
			return Unknown, err
		}
		if destLink == source {
			return Linked, nil
		}
		return WrongTarget, nil
	}
	return RealFile, nil
}

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

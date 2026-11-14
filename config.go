package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

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

func profileLinks(name string, config Config) ([]Link, error) {
	profile, ok := config.Profiles[name]
	if ok == false {
		return nil, fmt.Errorf("unknown profile %q", name)
	}

	links := []Link{}
	for _, moduleName := range profile.ModuleNames {
		module, ok := config.Modules[moduleName]
		if ok == false {
			return nil, fmt.Errorf("unknown module %q", moduleName)
		}

		for _, link := range module.Links {
			links = append(links, link)
		}
	}
	return links, nil
}

func expandHome(path string) (string, error) {
	rest, found := strings.CutPrefix(path, "~/")
	if found == false {
		return path, nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(home, rest), nil
}

func sourcePath(configPath string, path string) (string, error) {
	absConfig, err := filepath.Abs(configPath)
	if err != nil {
		return "", err
	}
	configDir := filepath.Dir(absConfig)
	return filepath.Join(configDir, path), nil
}

func loadConfig(path string) (Config, error) {
	config := Config{}
	_, err := toml.DecodeFile(path, &config)
	if err != nil {
		return Config{}, err
	}
	return config, nil
}

package main

import "fmt"

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

	gitConfigLink := Link{Source: "/home/theleberton/.dotfiles/git/config", Dest: "/home/theleberton/.gitconfig"}
	fmt.Println(gitConfigLink)
	fmt.Println(gitConfigLink.Source)
	fmt.Println(gitConfigLink.Dest)
	fmt.Println("\n")

	gitIgnoreLink := Link{Source: "/home/theleberton/.dotfiles/git/ignore", Dest: "/home/theleberton/.config/git/ignore"}
	fmt.Println(gitIgnoreLink)
	fmt.Println(gitIgnoreLink.Source)
	fmt.Println(gitIgnoreLink.Dest)
	fmt.Println("\n")

	gitModule := Module{Packages: []string{"git"}, Links: []Link{gitConfigLink, gitIgnoreLink}}
	fmt.Println(gitModule)
	fmt.Println(gitModule.Packages)
	fmt.Println(gitModule.Packages[0])
	fmt.Println(gitModule.Links)
	fmt.Println(gitModule.Links[0].Source)
	fmt.Println(gitModule.Links[0].Dest)
	fmt.Println("\n")

	ubuntuProfile := Profile{ModuleNames: []string{"zsh", "git", "nvim"}, PackageManager: "apt"}
	fmt.Println(ubuntuProfile)
	fmt.Println(ubuntuProfile.ModuleNames)
	fmt.Println(ubuntuProfile.PackageManager)
	fmt.Println(ubuntuProfile.ModuleNames[0])
	fmt.Println("\n")

	config := Config{Modules: map[string]Module{"git": gitModule}, Profiles: map[string]Profile{"ubuntu": ubuntuProfile}}
	fmt.Println(config)
	fmt.Println(config.Modules)
	fmt.Println(config.Modules["git"])
	fmt.Println(config.Modules["git"].Packages)
	fmt.Println(config.Modules["git"].Packages[0])
	fmt.Println(config.Modules["git"].Links)
	fmt.Println(config.Modules["git"].Links[0])
	fmt.Println(config.Modules["git"].Links[0].Source)
	fmt.Println(config.Modules["git"].Links[0].Dest)
	fmt.Println(config.Profiles)
	fmt.Println(config.Profiles["ubuntu"])
	fmt.Println(config.Profiles["ubuntu"].ModuleNames)
	fmt.Println(config.Profiles["ubuntu"].ModuleNames[0])
}

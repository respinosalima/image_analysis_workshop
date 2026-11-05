# Session 1: Installation of Python, uv, git, GitHub and AI coding assistants.

## Editor: Command line Interface (CLI) or VS code
There are multiple ways to interact with the tools that will be used in the workshop.  The preferred way is to use the Command Line Interface (CLI) also often called Terminal.  Many different versions of the CLI exist.  The CLI is the preferred way since it gives you the most flexibility and the most control, but some people greatly prefer a graphical interface.  To do things without a CLI, we will try to create instructions to use VS Code when possible.  

### CLI Installation (preferred option)
#### Windows
You can either use the built-in PowerShell or (preferred) install Git Bash (you will need to install Git later in any case).  Download [here](https://git-scm.com/install/windows) and install.
#### Mac and Linux

Use the Terminal application provided by your OS.  One the Mac, you can find it in "Applications/Utilities".  Drag the icon to the task bar for easier future access.

### VSCode installation (alternate option)
[Download and install](https://code.visualstudio.com/).  Note that VSCode (Visual Studio Code) is not the same thing as Visual Studio, Microsoft's separate full-featured IDE.



## AI coding assistants
Coding assistants are applications that run on your own computer, inspect the files in your working directory, and take your input (prompts) and convert them into running code.  Having access to one of these is critical to follow this workshop.  Regretfully, use of these will usually cost money.  There are currently two good options:
* [Claude Code from Anthropic](https://claude.com/product/claude-code).  Download and install the appropriate version (Terminal or VS Code).  You will need a subscription to use Claude Code.  Claude has a program that provides PIs with 23 free accounts at the Pro level.  If your PI has not signed up for this, please ask them to do so by going [here](https://claude.ai/labs-verification/attestation).  I failed to qualify as a PI (no idea why), so it may not always work.  I know of at least one PI who may have extra slots and will be willing to give those out, so contact me if your PI fails to qualify.  In the worst case, you could pay the $20 for a month's subscription yourself and ask your PI to reimburse you.
* [Codex from OpenAI](https://chatgpt.com/codex/).  Monthly subscriptions cost $20.  UCSF gives access to Codex; however, it will still bill you (or your PI) for its use.  If you want to go this route, you will first need to [sign up for UCSF ChatGPT Enterprise](https://ai.ucsf.edu/ucsf-chatgpt-enterprise-faqs#paragraph-2271), and take the UCSF SPARK-AI Foundations training within 60 days.  You will also need to request credits (at $0.06 per credit) that will be consumed by your Codex usage (I have no idea how many credits you will end up using).


### Python and uv
We will use the extremely fast package manager "uv" to handle Python environments.  Full instructions can be found [here](https://docs.astral.sh/uv/getting-started/installation/).  Short instructions:
#### Windows: 
Open PowerShell.  Copy and paste the following command:

```text
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### MacOS and Linux:
Open a Terminal (CLI) and paste:

```text
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If your system does not have curl, you can use wget:

```text
wget -qO- https://astral.sh/uv/install.sh | sh
```


### Git
Your AI code assistant will generate code that you will need to maintain in a source code repository.  We will be using git.  If you have not yet installed git, you can do so as follows:

#### Windows
Install Git Bash.  Download [here](https://git-scm.com/install/windows) and install.  (You already did this above if you chose Git Bash as your CLI.)

#### Mac OS
Choose one of the following options for installing Git on macOS:

* Homebrew

Install [homebrew](https://brew.sh/) if you don't already have it, then:
```text
brew install git
```

* MacPorts (alternative to Homebrew, you need only need this if you do not use Homebrew)

Install MacPorts if you don't already have it, then:
```text
sudo port install git
```

* Xcode Command Line Tools

Apple ships a binary package of Git with Xcode Command Line Tools. You can install this via:
```text
xcode-select --install
```

* Installing git-gui (recommended)

If you would like to install git-gui and gitk, git's commit GUI and interactive history browser, you can do so using homebrew
```text
brew install git-gui
```

### Set your identity (this needs to be done once)
In a terminal, enter:
```text
git config --global user.name "Your Name"
```
and
```text
git config --global user.email "your.email@example.com"
```

## GitHub
Although not strictly necessary, you are highly encouraged to create an account on GitHub.  Visit [https://github.com](https://github.com), Create an account.  You may want to join [GitHub Education](https://github.com/education). 

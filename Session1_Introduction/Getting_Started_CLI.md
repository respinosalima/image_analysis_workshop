# Getting started (using the Terminal)

## Clone this GitHub repository to your own computer
* Open the Terminal application (or Git Bash on Windows).
* Navigate to the place where you want to store the materials for this course.  Personally, I always make a directory called "projects" in my home directory, and that is where I keep my source code repositories. To do so in the Terminal (or Git Bash), type:

```text
mkdir projects
cd projects
```
* Fork this repository

Log in to [GitHub](https://github.com). On the [GitHub image_analysis_workshop](https://github.com/UCSF-CALM/image_analysis_workshop) page find the "Fork" button (near the right top) and click it. Create the fork under your own GitHub name ("your_github_name").  

* Clone this repository:
```text
git clone https://github.com/your_github_name/image_analysis_workshop.git
```
Make sure to change "your_github_name" to your GitHub user name.

* Move to the cloned repository:
```text
cd image_analysis_workshop
```

Add the UCSF_CALM repository as the "upstream" repository:
```text
git remote add upstream https://github.com/UCSF-CALM/image_analysis_workshop.git
```

## Create a git branch where you will keep your own work
Under the hood, git stores differences (diffs) between versions.  You create a new version by using the command ```git commit```.  However, you will want to add your own commits to your own "branch" (so that you can always go back to a pristine state).  To create your own branch, called "my_branch" use the command:
```text
git switch -c my_branch
```
Now create a test file and add some text to it:
```text
echo "The first content for my own branch" > test.txt
```
Add this file to the list of files to be committed:
```text
git add test.txt
```
And then commit it:
```text
git commit -m "The first file added to my_branch is just a test file."
```

> IMPORTANT:
> Never commit passwords, secret keys, etc. to a git repository.  It is extremely 
> difficult to remove these from the repo completely, and pushing them to a site
> such as GitHub will make them publicly accessible.

You can now push this file to GitHub:
```text
git push
```
Note that the first time you "push" (to GitHub) you will need to tell the push command to create the branch:
```text
git push --set-upstream origin my_branch
```

Occasionally, there will be changes/additions in the "upstream" UCSF-CALM repository.  You can get these in your work branch using the following commands:
```text
git checkout main
git pull upstream main
git checkout my_branch
git merge main
```
Make sure not to change files that are in the "main" branch (which could result in merge conflicts).  

## Create a Python environment and test
Execute the following command:
```text
uv sync
```
This will create a (virtual) Python environment as specified in the file "pyproject.toml".  The specified packages will be downloaded and installed.  They are cached, so that if these packages are needed again later, they will not be downloaded again.   

Then run the test script using:
```text
 uv run src/show_image.py
 ```

Note, this command will not exit until you close the (napari) viewer.  If you would like to continue working on the command line while the Python script is running, you can do:

```text
uv run src/show_image.py &
```

Fun fact, you can actually skip "uv sync", uv will set up the environment also when you use "uv run". Next time you run the script, it will be much faster.


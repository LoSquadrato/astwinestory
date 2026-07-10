# StoryLoom — CLI Editor for Interactive Stories

StoryLoom is a tool for parsing, translating, and converting interactive stories in Twine (`.twee`) format.
The idea is to provide a CLI for serializing stories into a JSON intermediate format, which can then be translated or processed and re-exported into `.twee` files.

---

## Getting Started

### Requirements
> Python 3.11 or higher

### Installation

```shell
git clone https://github.com/LoSquadrato/StoryLoom.git
cd StoryLoom
pip install -r requirements.txt
```
### Usage

Have a `.twee` file ready and the [format JSON file](##JSON-Library) of the story format inside the `core/assets/formats` folder, then run the following command:

```shell
python3 main.py story.twee
```
REPL Input:
* Select Output Format from the JSON file provided inside the `core/assets/formats` folder
* Select Function from a list menu
* Select Output File Name (or use the one suggested by the program)

## WARNING:
* StoryLoom is still in development and not yet stable. **Make a backup of your work before using it.** 

* **Edit only story that's are your own**, or that you have permission to modify. Every copyrighted work is protected by law, and StoryLoom is not responsible for any illegal use of the software.  

---

## Documentation

In the docs folder you can find a documentation (WIP) explained the project, including the architecture, the data structures, and the algorithms used.

---

## Future Work

* Finalize the AST structure and the parsing logic.
* Implement the conversion between different Twine formats.
* Implement the translation logic, including the extraction of text nodes and re-insertion of translated text.
* Implement a buffering system for reading and writing large stories, to avoid memory issues.
* Implement a GUI for easy story management.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Make sure to follow the coding style and include tests for any new features or bug fixes.
Expecially for the GUI, if you have experience with GUI frameworks (like PyQt, Tkinter, or Kivy), your help would be greatly appreciated 🙏.

---

### License

**License**: GPL v3 (GNU General Public License v3)

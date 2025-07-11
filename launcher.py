import sys
import os
import subprocess
import yaml
import tkinter as tk
from tkinter import messagebox
import traceback


def show_detailed_error(title, message, exception=None):
  """Display a detailed error message with stack trace in a popup."""
  if exception:
    stack_trace = traceback.format_exc()
    full_message = f"{message}\n\nDetails:\n{str(exception)}\n\nStack Trace:\n{stack_trace}"
  else:
    full_message = message
  messagebox.showerror(title, full_message)


def main():
  """
  A Python program that presents a typeahead bookmark launcher GUI.
  It loads bookmark definitions from bookmarks.yml and launches URLs via handlers.
  All keys and values are explicitly converted to strings to avoid type mismatches.
  """
  try:
    if len(sys.argv) != 6:
      raise ValueError("Usage: python launcher.py <foreground_exe> <x> <y> <width> <height>")

    foreground_exe = str(sys.argv[1])
    try:
      win_x = int(sys.argv[2])
      win_y = int(sys.argv[3])
      win_width = int(sys.argv[4])
      win_height = int(sys.argv[5])
    except ValueError:
      raise ValueError("Geometry arguments must be integers: " + str(sys.argv[2:]))

    script_directory = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(script_directory, "bookmarks.yml")

    try:
      with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    except FileNotFoundError:
      raise FileNotFoundError(f"YAML file not found: {yaml_path}")
    except yaml.YAMLError as e:
      raise yaml.YAMLError(f"Invalid YAML format in {yaml_path}: {str(e)}")

    if not isinstance(data, dict):
      raise ValueError(f"YAML file {yaml_path} must contain a dictionary at the root level")

    matched_category = None
    handler_path = None
    for category_name, category_dict in data.items():
      category_name = str(category_name)
      if not isinstance(category_dict, dict) or "handlers" not in category_dict:
        continue
      for key, full_path in category_dict["handlers"].items():
        key = str(key)
        full_path = str(full_path)
        if key.lower() == foreground_exe.lower():
          matched_category = category_name
          handler_path = full_path
          break
      if matched_category:
        break

    if matched_category is None or handler_path is None:
      messagebox.showinfo("No matching category", f"No category found for EXE: {foreground_exe}")
      sys.exit(1)

    bookmarks_dict = data[matched_category].get("bookmarks", {})
    if not isinstance(bookmarks_dict, dict):
      raise ValueError(f"Bookmarks in category '{matched_category}' must be a dictionary")

    bookmark_items = []
    for key, props in bookmarks_dict.items():
      key = str(key)
      if not isinstance(props, dict) or "url" not in props:
        raise ValueError(f"Bookmark '{key}' in category '{matched_category}' must be a dictionary with a 'url' key")
      display_name = str(props.get("dsp", key))
      url = str(props["url"])
      bookmark_items.append((key, display_name, url))
    bookmark_items.sort(key=lambda item: str(item[0]))

    root = tk.Tk()
    root.title("Bookmark Launcher")
    root.configure(bg="#333333")
    root.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")

    entry_var = tk.StringVar()
    entry = tk.Entry(root,
      textvariable=entry_var,
      bg="#555555",
      fg="#FFFFFF",
      insertbackground="#00FF00",
      insertwidth=4,
      insertofftime=0,
      font=("Courier New", 12),
      highlightthickness=0,
      bd=0)
    entry.pack(fill=tk.X, padx=8, pady=8)

    listbox = tk.Listbox(root,
      bg="#333333",
      fg="#FFFFFF",
      font=("Courier New", 12),
      selectbackground="#666666",
      selectforeground="#FFFFFF",
      highlightthickness=0,
      bd=0)
    listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))

    def update_listbox(*args):
      typed_text = str(entry_var.get().strip().lower())
      listbox.delete(0, tk.END)
      potential_matches = []
      exact_match_index = -1
      for (key, dsp, url) in bookmark_items:
        if typed_text in str(key).lower() or typed_text in str(dsp).lower():
          potential_matches.append((key, dsp, url))
      if potential_matches:
        potential_matches.sort(key=lambda item: str(item[0]))
        for idx, (key, dsp, url) in enumerate(potential_matches):
          listbox.insert(tk.END, f"[{str(key)}] - {str(dsp)} - {str(url)}")
          if typed_text == str(key).lower():
            exact_match_index = idx
        if exact_match_index >= 0:
          listbox.select_set(exact_match_index)
          listbox.activate(exact_match_index)
        else:
          listbox.select_set(0)
          listbox.activate(0)

    def launch_bookmark(event=None):
      """
      Launch whichever bookmark is highlighted in the Listbox.

      The Listbox always shows a filtered and alphabetically-sorted view
      of `bookmark_items`, so we rebuild that same view here to map the
      Listbox row index back to its underlying (key, dsp, url) tuple.

      Pressing <Enter> without a selection or with an out-of-range index
      is ignored gracefully.
      """
      typed_text = str(entry_var.get().strip().lower())

      # Nothing highlighted → nothing to launch
      selection = listbox.curselection()
      if not selection:
        return
      selected_index = selection[0]

      # Re-create the list currently visible in the Listbox
      visible_items = [
        (key, dsp, url)
        for (key, dsp, url) in bookmark_items
        if typed_text in str(key).lower() or typed_text in str(dsp).lower()
      ]
      if selected_index >= len(visible_items):
        return

      key, dsp, url = visible_items[selected_index]
      cmd = [str(handler_path), os.path.normpath(str(url))]
      try:
        subprocess.Popen(cmd, shell=False)
      except FileNotFoundError as e:
        show_detailed_error(
          "Launch Error",
          f"Could not launch {handler_path}. Verify the executable path.",
          e,
        )
      except subprocess.SubprocessError as e:
        show_detailed_error("Launch Error", f"Error launching {url}", e)
      finally:
        root.destroy()

    def close_window(event=None):
      root.destroy()

    def check_focus():
      if root.focus_get() is None:
        root.destroy()
      else:
        root.after(500, check_focus)

    def on_focus_out(event):
      root.after(500, check_focus)

    def on_focus_in(event):
      root.after_cancel(check_focus)

    def move_selection(event):
      current = listbox.curselection()
      if not current:
        if listbox.size() > 0:
          listbox.select_set(0)
          listbox.activate(0)
      else:
        index = current[0]
        if event.keysym == "Up" and index > 0:
          listbox.select_clear(index)
          listbox.select_set(index - 1)
          listbox.activate(index - 1)
        elif event.keysym == "Down" and index < listbox.size() - 1:
          listbox.select_clear(index)
          listbox.select_set(index + 1)
          listbox.activate(index + 1)
      return "break"

    entry_var.trace("w", update_listbox)
    root.bind("<Return>", launch_bookmark)
    root.bind("<Escape>", close_window)
    entry.bind("<Up>", move_selection)
    entry.bind("<Down>", move_selection)
    root.bind("<FocusOut>", on_focus_out)
    root.bind("<FocusIn>", on_focus_in)

    update_listbox()
    entry.focus()
    root.after(500, check_focus)
    root.mainloop()

  except yaml.YAMLError as e:
    show_detailed_error("YAML Parsing Error", "Failed to parse bookmarks.yml due to invalid format.", e)
    sys.exit(1)
  except FileNotFoundError as e:
    show_detailed_error("File Error", "Required file could not be found.", e)
    sys.exit(1)
  except ValueError as e:
    show_detailed_error("Configuration Error", "Invalid configuration or input.", e)
    sys.exit(1)
  except Exception as e:
    show_detailed_error("Unexpected Error", "An unexpected error occurred while running the launcher.", e)
    sys.exit(1)


if __name__ == "__main__":
  main()

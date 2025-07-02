import os
import shutil
import tempfile
def create_directory(path,mode=0o755):
    """
    Makes a new folder at the given path with the given permissions.

    Arguments:
        path (str): The name or location where you want to create the folder.
        mode (int): The permissions for the folder (like 0o755). 

    Errors it raises:-
        FileExistsError: If the folder already exists.
        OSError: If there's a problem from the operating system.
    """
    try:
        os.mkdir(path, mode)
        print(f"Directory '{path}' created with permissions {oct(mode)}")
    except FileExistsError:
        print(f"Directory '{path}' already exists.")
    except Exception as e:
        print(f" Error creating directory '{path}': {e}")
def copy_file(src,dst)
     """
    Copies a file from src to dst.

    Arguments:
        src (str): The source file path.
        dst (str): The destination file path.

    Raises:
        FileNotFoundError: If the source file does not exist.
        PermissionError: If the copy fails due to permission issues.
    """
     try:
         shutil.copy2(src,dst)
         print(f"copied file from '{src}'to '{dst}'")
       except FileNotFoundError:
        print(f"Source file '{src}' not found.")
    except PermissionError:
        print(f"Permission denied while copying to '{dst}'.")
    except Exception as e:
        print(f"Error copying file: {e}")
def render_template(template_path,output_path,context):
      """
    Replaces placeholders in a template file with context values.

    Arguments:
        template_path (str): Path to the template file.
        output_path (str): Where to write the rendered file.
        context (dict): A dictionary of placeholder-value pairs.
    """
      try:
                   with open(template_path, 'r') as f:
            content = f.read()
        for key, value in context.items():
            content = content.replace(f"{{{{ {key} }}}}", str(value))
        with tempfile.NamedTemporaryFile('w', delete=False, dir=os.path.dirname(output_path)) as tmp:
            tmp.write(content)
            tmp.flush()
            os.replace(tmp.name, output_path)
        print(f"Rendered template written to '{output_path}'")
    except FileNotFoundError:
        print(f"Template file '{template_path}' not found.")
    except PermissionError:
        print(f"Permission denied while writing to '{output_path}'.")
    except Exception as e:
        print(f"Error rendering template: {e}")

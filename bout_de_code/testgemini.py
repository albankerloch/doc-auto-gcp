import os
import google.generativeai as genai


def list_files(directory):
    try:
        file_paths = []
        for root, dirs, files in os.walk(directory):
            for name in files:
                full_path = os.path.join(root, name)
                if os.path.isfile(full_path):
                    relative_path = os.path.relpath(full_path, directory)
                    file_paths.append(relative_path)
        return file_paths
    except FileNotFoundError:
        print(f"Error: Directory not found at '{directory}'")
        return None
    except Exception as e:
        print(f"An error occurred while listing files: {e}")
        return None


def write_new_content_file(file_content, file_path):
    # os.remove(file_path)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(file_content)


def read_file_to_variable(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            file_content = file.read()
        return file_content
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None


def useGemini(file_content):
    ex1_entry = read_file_to_variable("examples/test.c")
    ex1_exit = read_file_to_variable("examples/test2.c")
    ex2_entry = read_file_to_variable("examples/split.c")
    ex2_exit = read_file_to_variable("examples/split2.c")
    ex3_entry = read_file_to_variable("examples/ft_sort_params.c")
    ex3_exit = read_file_to_variable("examples/ft_sort_params2.c")
    genai.configure(api_key="AIzaSyBnND6kLJ26lylFnNX8Aco0g0-3bPHATSo")
    model = genai.GenerativeModel("gemini-1.5-pro-002")
    response = model.generate_content(
        f"""{file_content}, analyse moi le code source de mon fichier pour en extraire les signatures des structures, fonctions, typedef, def et enum, pour commenter ces signatures sans changer le code source juste en incorporant les commentaires en plus avec un format compatible avec doxygen.
        Je ne veux pas que tu utilises les balises @author, @var ou @date.
        Ecrit toujours le commentaire au dessus de la signature associee mais ecrit evidemment le code source entier.
        Ne donne pas de recommandations.
        quand tu écrit ne rajoute pas de ```cpp ``` ou ```c``` devant le code source.
        Car aprés je réécris tous dans un fichier .c
        Je te donne un exemple de ce que je veux:
        entrée {ex1_entry} sortie {ex1_exit}
        entrée {ex2_entry} sortie {ex2_exit}
        entrée {ex3_entry} sortie {ex3_exit}
        """
    )
    return response.text


def main():

    listPath = list_files("C00")
    while len(listPath) > 0:
        elem = listPath.pop()
        if elem.endswith(".c"):
            file_content = read_file_to_variable(elem)
            response = useGemini(file_content)
            write_new_content_file(response, elem)


if __name__ == "__main__":
    main()

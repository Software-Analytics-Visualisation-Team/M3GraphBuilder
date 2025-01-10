# M3GraphBuilder

M3GraphBuilder is a Python tool with a command line interface (CLI) that builds a [labeled property graph (LPG) representation for software structure](https://github.com/rsatrioadi/phd/blob/main/representation.md) from a [M3 model](https://www.rascal-mpl.org/docs/Packages/Clair/API/lang/cpp/M3/). The M3 model is obtained by parsing C or C++ code and contains rich information about the source code.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
    - [Running Locally](#running-locally)
    - [Running in Docker](#running-in-docker)
- [M3GB Arguments](#m3gb-arguments)
    - [`create-graph`](#create-graph)
    - [`create-hierarchy`](#create-hierarchy)
    - [`merge-graph`](#merge-graphs)
    - [`merge-hierarchies`](#merge-hierarchies)
- [Examples](#examples)
  - [Creating a Graph](#creating-a-graph)
  - [Creating a Hierarchy](#creating-a-hierarchy)
  - [Merging Hierarchies](#merging-hierarchies)
- [Configuration](#configuration)
- [Visualising the graph](#visualising-the-graph)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

# Prerequisites
- **Python 3.6** or higher to run locally
- **Docker**: for running in Docker
- **M3 Models** of the source code you want to visualise, in json. To generate such a model, you can use the [Alpha tool](https://github.com/LightFLP/Alpha), based on the meta-programming language [Rascal](https://www.rascal-mpl.org/), or implement your own parser.

# Installation

To install M3GraphBuilder, clone the repository and install the required dependencies:

```sh
git clone https://github.com/your-repo/M3GraphBuilder.git
```

## Running Locally

If you intend to run the tool locally, install the required dependencies:
```sh
cd M3GraphBuilder
pip install -r requirements.txt
```
## Running in Docker

To build the Docker image for M3GraphBuilder, run the following command in the directory containing the Dockerfile:

```sh
docker build . -t m3gb-app
```

This command creates a Docker image named `m3gb-app`.

Then to run the M3GraphBuilder using Docker Compose, use the following command. This will create a container, execute the M3GraphBuilder process and remove the container afterwards.:

```sh
docker-compose run --rm graphbuilder <M3GB argument>
```

Replace `<M3GB argument>` with the desired command and arguments for M3GraphBuilder. For example, to create a graph, you can use:

```sh
docker-compose run --rm graphbuilder create-graph -m "/my_path/input/m3_model.json" -v
```

This will create a graph in the `output/ClassViz` folder that can visualised using ClassViz or BubbleTeaViz. The `-v` flag will create a `<graph name>_clean.lpg.json` file if any discrepencies were found in the resulting graph due to the quality of the C++ models.

# M3GB Arguments

## `create-graph`
Create a ClassViz graph from a M3 model.

**Options:**
- `-m MODEL, --model MODEL`  
    Path to the model file.
- `-n NAME, --name NAME` (Optional)  
    Name of the generated graph.
- `-o OUTPUT, --output OUTPUT` (Optional)
    Output folder for the graph.
- `-v, --validate` (Optional) 
    Validate that all nodes in the edges exist.

## `create-hierarchy`
Extract layered nodes and edges from a ClassViz graph to be visualised in ARViSAN.

**Options:**
- `-g GRAPH, --graph GRAPH`  
    Path to the graph file.
- `-o OUTPUT, --output OUTPUT`(Optional)
    Output folder for components.

## `merge-graphs`
Merge two graphs.

## `merge-hierarchies`
Merge two sets of hierarchies (both nodes and edges). This can be used to merge two subsystems/modules of the same software system, so that they can be visualised together in ARViSAN. 

**Options:**
- `-h, --help`  
    Show this help message and exit.
- `-n1 NODES1, --nodes1 NODES1`  
    Path of the first nodes files.
- `-n2 NODES2, --nodes2 NODES2`  
    Path of the second nodes files.
- `-n3 NODES3, --nodes3 NODES3`  
    Name of the produced nodes and edges files. For example, *nodes3 argument*-nodes.csv.
- `-o OUTPUT, --output OUTPUT` (Optional)
    Output path for the merged nodes and edges.
- `-s, --separate` (Optional)
    Separate all common nodes in both hierarchies together.

# Examples

## Creating a Graph
```sh
python -m M3GraphBuilder create-graph -m "/my_path/m3_model.json" -n "MyGraph" -o "/output_path"
```
## Creating a Hierarchy
```sh
python -m M3GraphBuilder create-hierarchy -g "/my_path/graph.json" -o "/output_path"
```
## Merging Hierarchies
```sh
python -m M3GraphBuilder merge-hierarchies -n1 "/path/nodes1.csv" -n2 "/path/nodes2.csv" -n3 "merged" -o "/output_path"
```

# Configuration

M3GraphBuilder can be configured using the following environment variables in a config.ini file. An example config can be found in the repository.

- `[PROJECT]`:
    - `name`: The name of a system used for creating a hierarchy. This name will be used for the domain (top) node in ARViSAN.
    - `desc`: The description of the system.
- `[input]`:
    - `path`: The path to the folder containing the input files. (If you change this value, and want to run M3GB in Docker, change it in the `docker-compose.yaml` as well)
- `[output]`:
    - `path`: The path to the folder in which the graphs and hierarchies will be saved. (If you change this value, and want to run M3GB in Docker, change it in the `docker-compose.yaml` as well)
- `[logging]`:
- `path`: The path to the folder in which the logs will be saved. (If you change this value, and want to run M3GB in Docker, change it in the `docker-compose.yaml` as well)
- `verbose`: A boolean for the verbosity of the logs. Set to `True` for more detailed logs, otherwise set to `False`.

# Visualising the graph
The graphs can be visualised and interacted with, in [ClassViz](https://github.com/rsatrioadi/classviz) by downloading and running the tool, or simply loaded in the [running version of the tool](https://rsatrioadi.github.io/classviz/), and BubbleTeaViz. The hierarchies can be visualised in ARViSAN.

# Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
# Contact

If you have any questions or need help, please contact us at [f.zamfirov@tue.nl](mailto:f.zamfirov@tue.nl)
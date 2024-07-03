# C3GraphBuilder

This is a python tool using a command line interface (CLI) which can be used to build a [labeled property graph (LPG) representation for software structure](https://github.com/rsatrioadi/phd/blob/main/representation.md) out of a [M3 model](https://www.rascal-mpl.org/docs/Packages/Clair/API/lang/cpp/M3/) - a model obtained by parsing C or C++ code, containing rich information about the source code.

## Using C3GraphBuilder
A graph can be built by running the following command:

```python
python -m C3GraphBuilder -m_path "/my_path/m3_model.json"
```

The graph name and the location where it will be stored can be modified with additional command line parameters. For a list of the different parameters do:

```python
python -m C3GraphBuilder --help
```

## Generating a M3 model from source code
To generate such a model, a parser must be used. You can use the [Alpha]() parser, based on the meta-programming language [Rascal](https://www.rascal-mpl.org/), or implement your own parser.

## Visualising the graph
The built graph can be visualised and interacted with, in [ClassViz](https://github.com/rsatrioadi/classviz) by downloading and running the tool, or simply loaded in the [running version of the tool](https://rsatrioadi.github.io/classviz/)
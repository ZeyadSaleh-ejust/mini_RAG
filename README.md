# mini_RAG

this is a minimal implementation of RAG model for question answering 

## Requirements
- python 3.8 or later

#### Install python using MiniConda

1) Download and install MiniConda from [here](https://www.anaconda.com/docs/getting-started/miniconda/main#quick-command-line-install)
2) create a new environment using the following command:
```bash
$ conda create -n mini-rag python=3.8 -y
```
3) Activate the environment:
```bash
$ conda activate mini-rag
```
### (Optional) Setup your command line for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$"
```

## Installation

### Install the required packages

```bash
$ pip install -r requirements.txt
```

### Setup the environment variables

```bash
$ cp .env.example .env
```

set your environment variable in the `.env` file like `OPENAI_API_KEY` value.
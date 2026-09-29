"""Pacote da aplicação Cantina+.

Inicie com ``python run.py`` na pasta do projeto.
"""
__title__ = "Cantina+"
__version__ = "2.0.0"
__author__ = "Projeto Cantina Escolar"

from .database import Database

__all__ = ["Database", "__title__", "__version__", "__author__"]
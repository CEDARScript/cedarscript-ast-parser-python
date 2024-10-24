import pytest
from cedarscript_ast_parser import CEDARScriptASTParser


def test_can_instantiate_parser():
    """Test that we can create a CEDARScriptASTParser instance"""
    CEDARScriptASTParser()

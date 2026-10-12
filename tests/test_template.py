"""Tests for template parameter parsing and substitution."""

from mnemo.template import extract_parameters, substitute_parameters


def test_extract_parameters():
    text = "docker run -d -p {port}:{port} --name {container_name} {{image}} <tag>"
    params = extract_parameters(text)
    assert params == ["port", "container_name", "image", "tag"]


def test_substitute_parameters():
    template = "curl -X POST {url} -H 'Authorization: Bearer {token}'"
    values = {"url": "https://api.example.com", "token": "secret123"}
    result = substitute_parameters(template, values)
    assert (
        result
        == "curl -X POST https://api.example.com -H 'Authorization: Bearer secret123'"
    )


def test_substitute_partial():
    template = "git checkout -b {branch_name} origin/{remote}"
    values = {"branch_name": "feature-x"}
    result = substitute_parameters(template, values)
    assert result == "git checkout -b feature-x origin/{remote}"

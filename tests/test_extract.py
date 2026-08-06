"""Lifting registry entries out of source without importing it.

``error-codes.md`` requires a registry entry to be a literal at module scope — never assembled from
variables, f-strings, loops, or factories — and says the restriction exists so that a catalog can be
extracted by static analysis. This is that static analysis, so it enforces the restriction rather
than working around it (``this.i`` @tjs63f): anything it cannot read as a literal is reported as a
problem, never guessed at and never silently dropped.
"""

import textwrap

from bakobo.errors.extract import extract_module


def lift(source: str, path: str = "src/pkg/errors.py", repo: str = "pkg"):
    return extract_module(textwrap.dedent(source), repo=repo, path=path)


def test_a_full_entry_is_lifted_with_every_field_and_its_origin():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        SIG_INVALID = ErrorCode(
            "e.proof.credential-sig.f",
            "The authority evidence carries a signature that does not verify.",
            detail="The signature on credential {credential} does not verify.",
            args=("credential",),
            hint="Confirm the credential was issued by the AID you expect.",
        )
        '''
    )
    assert problems == []
    (entry,) = entries
    assert entry.code == "e.proof.credential-sig.f"
    assert entry.title == "The authority evidence carries a signature that does not verify."
    assert entry.detail == "The signature on credential {credential} does not verify."
    assert entry.args == ("credential",)
    assert entry.hint == "Confirm the credential was issued by the AID you expect."
    assert entry.symbol == "SIG_INVALID"
    assert entry.repo == "pkg"
    assert entry.path == "src/pkg/errors.py"
    assert entry.line == 4


def test_an_entry_with_only_a_code_and_a_title_leaves_the_rest_empty():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        NO_SIG = ErrorCode("e.input.missing.sig.f", "The request carries no signature to check.")
        '''
    )
    assert problems == []
    (entry,) = entries
    assert entry.detail is None
    assert entry.args == ()
    assert entry.hint is None


def test_code_and_title_may_be_passed_by_keyword():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        NO_SIG = ErrorCode(title="No signature.", code="e.input.missing.sig.f")
        '''
    )
    assert problems == []
    assert entries[0].code == "e.input.missing.sig.f"
    assert entries[0].title == "No signature."


def test_strings_split_across_lines_are_read_as_one_literal():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        SPLIT = ErrorCode(
            "e.input.format.sig.f",
            "A title.",
            detail=(
                "The first half, "
                "and the second."
            ),
        )
        '''
    )
    assert problems == []
    assert entries[0].detail == "The first half, and the second."


def test_an_alias_of_the_import_is_still_recognised():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode as EC

        NO_SIG = EC("e.input.missing.sig.f", "No signature.")
        '''
    )
    assert problems == []
    assert entries[0].code == "e.input.missing.sig.f"


def test_a_qualified_call_through_the_module_is_still_recognised():
    entries, problems = lift(
        '''
        from bakobo import errors

        NO_SIG = errors.ErrorCode("e.input.missing.sig.f", "No signature.")
        '''
    )
    assert problems == []
    assert entries[0].code == "e.input.missing.sig.f"


def test_a_call_to_something_else_is_ignored_rather_than_reported():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        THING = SomethingElse("e.input.missing.sig.f", "No signature.")
        '''
    )
    assert entries == []
    assert problems == []


def test_a_call_on_the_result_of_another_call_is_not_a_construction():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        THING = factory()("e.input.missing.sig.f", "No signature.")
        '''
    )
    assert entries == []
    assert problems == []


def test_more_positional_arguments_than_fields_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        BAD = ErrorCode("e.input.format.sig.f", "A title.", "d", ("a",), "hint", "sixth")
        '''
    )
    assert entries == []
    assert "positional" in problems[0].reason


def test_a_field_given_both_positionally_and_by_keyword_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        BAD = ErrorCode("e.input.format.sig.f", "A title.", code="e.input.format.other.f")
        '''
    )
    assert entries == []
    assert "code" in problems[0].reason


def test_a_field_assembled_from_a_variable_is_a_problem_not_an_entry():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        HINT = "Shared advice."
        SHARED = ErrorCode("e.input.format.sig.f", "A title.", hint=HINT)
        '''
    )
    assert entries == []
    (problem,) = problems
    assert problem.symbol == "SHARED"
    assert problem.line == 5
    assert "hint" in problem.reason


def test_a_field_built_by_an_f_string_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        WHAT = "sig"
        BAD = ErrorCode("e.input.format.sig.f", f"A {WHAT} title.")
        '''
    )
    assert entries == []
    assert "title" in problems[0].reason


def test_an_entry_declared_inside_a_function_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        def make():
            return ErrorCode("e.input.format.sig.f", "A title.")
        '''
    )
    assert entries == []
    assert "module scope" in problems[0].reason


def test_an_entry_that_is_never_assigned_to_a_name_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        ErrorCode("e.input.format.sig.f", "A title.")
        '''
    )
    assert entries == []
    assert problems[0].symbol is None


def test_an_entry_bound_to_two_names_at_once_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        A = B = ErrorCode("e.input.format.sig.f", "A title.")
        '''
    )
    assert entries == []
    assert problems != []


def test_an_annotated_assignment_is_a_normal_entry():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        NO_SIG: ErrorCode = ErrorCode("e.input.missing.sig.f", "No signature.")
        '''
    )
    assert problems == []
    assert entries[0].symbol == "NO_SIG"


def test_an_entry_missing_its_title_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        BAD = ErrorCode("e.input.format.sig.f")
        '''
    )
    assert entries == []
    assert "title" in problems[0].reason


def test_an_entry_carrying_an_unknown_field_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        BAD = ErrorCode("e.input.format.sig.f", "A title.", status=400)
        '''
    )
    assert entries == []
    assert "status" in problems[0].reason


def test_an_entry_splatted_from_a_dict_is_a_problem():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        BAD = ErrorCode("e.input.format.sig.f", "A title.", **extras)
        '''
    )
    assert entries == []
    assert problems != []


def test_an_illegal_code_in_source_is_a_problem_rather_than_a_crash():
    entries, problems = lift(
        '''
        from bakobo.errors import ErrorCode

        BARE = ErrorCode("e.proof.f", "A bare descriptor is a category, never a code.")
        '''
    )
    assert entries == []
    assert "e.proof.f" in problems[0].reason


def test_a_file_that_does_not_parse_is_a_problem_rather_than_a_crash():
    entries, problems = lift("this is not python (")
    assert entries == []
    assert problems[0].line >= 1

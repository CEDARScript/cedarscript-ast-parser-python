from enum import StrEnum, auto
from typing import TypeAlias, NamedTuple, Union

from tree_sitter import Parser
import cedarscript_grammar
from dataclasses import dataclass

__all__ = ['CEDARScriptASTParser', 'ParseError', 'Command']


class ParseError(NamedTuple):
    command_ordinal: int
    message: str
    line: int
    column: int
    suggestion: str

    def __str__(self):
        return (
            f"<error-details><error-location>COMMAND #{self.command_ordinal}{f'; LINE #{self.line}' if self.line else ''}{f'; COLUMN #{self.column}' if self.column else ''}</error-location>"
            f"<type>PARSING (no commands were applied at all)</type><description>{self.message}</description>"
            f"<suggestion>{f"{self.suggestion} " if self.suggestion else ""}"
            "(NEVER apologize; just take a deep breath, re-read grammar rules (enclosed by <grammar.js> tags) "
            "and fix you CEDARScript syntax)</suggestion></error-details>"
        )


# <location>


class BodyOrWhole(StrEnum):
    BODY = auto()
    WHOLE = auto()


MarkerType = StrEnum('MarkerType', 'LINE VARIABLE FUNCTION CLASS')
RelativePositionType = StrEnum('RelativePositionType', 'AT BEFORE AFTER INSIDE')

@dataclass
class Marker:
    type: MarkerType
    value: str
    offset: int | None = None

    def __str__(self):
        result = f"{self.type.value} '{self.value}'"
        if self.offset is not None:
            result += f" at offset {self.offset}"
        return result


class RelativeMarker(Marker):
    qualifier: RelativePositionType

    def __init__(self, qualifier: RelativePositionType, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qualifier = qualifier

    def __str__(self):
        result = super().__str__()
        match self.qualifier:
            case RelativePositionType.AT:
                pass
            case _:
                result = f'{result} ({self.qualifier})'
        return result


@dataclass
class Segment:
    start: RelativeMarker
    end: RelativeMarker

    def __str__(self):
        return f"segment from {self.start} to {self.end}"


MarkerOrSegment: TypeAlias = Marker | Segment
Region: TypeAlias = BodyOrWhole | MarkerOrSegment
RegionOrRelativeMarker: Region | RelativeMarker
# <file-or-identifier>


@dataclass
class WhereClause:
    field: str
    operator: str
    value: str


@dataclass
class SingleFileClause:
    file_path: str


@dataclass
class IdentifierFromFile(SingleFileClause):
    where_clause: WhereClause
    identifier_type: str  # VARIABLE, FUNCTION, CLASS
    offset: int | None = None

    def __str__(self):
        result = f"{self.identifier_type.lower()} (self.where_clause)"
        if self.offset is not None:
            result += f" at offset {self.offset}"
        return f"{result} from file {self.file_path}"


FileOrIdentifierWithin: TypeAlias = SingleFileClause | IdentifierFromFile

# </file-or-identifier>

# </location>


# <editing-clause>

@dataclass
class RegionClause:
    region: Region


@dataclass
class ReplaceClause(RegionClause):
    pass


@dataclass
class DeleteClause(RegionClause):
    pass


@dataclass
class InsertClause:
    insert_position: RelativeMarker


@dataclass
class MoveClause(DeleteClause, InsertClause):
    to_other_file: SingleFileClause | None = None
    relative_indentation: int | None = None


EditingAction: TypeAlias = ReplaceClause | DeleteClause | InsertClause | MoveClause

# </editing-clause>


# <command>

@dataclass
class Command:
    type: str

    @property
    def files_to_change(self) -> tuple[str, ...]:
        return ()

# <file-command>


@dataclass
class FileCommand(Command):
    file_path: str

    @property
    def files_to_change(self) -> tuple[str, ...]:
        return (self.file_path,)


@dataclass
class CreateCommand(FileCommand):
    content: str

@dataclass
class RmFileCommand(FileCommand):
    pass


@dataclass
class MvFileCommand(FileCommand):
    target_path: str

    @property
    def files_to_change(self) -> tuple[str, ...]:
        return super().files_to_change + (self.target_path,)

# </file-command>


@dataclass
class UpdateCommand(Command):
    target: FileOrIdentifierWithin
    action: EditingAction
    content: str | None = None

    @property
    def files_to_change(self) -> tuple[str, ...]:
        result = (self.target.file_path,)
        match self.action:
            case MoveClause(to_other_file=target_file):
                if target_file:
                    result += (target_file,)
        return result


@dataclass
# TODO
class SelectCommand(Command):
    target: Union['FileNamesPathsTarget', 'OtherTarget']
    source: Union['SingleFileClause', 'MultiFileClause']
    where_clause: WhereClause | None = None
    limit: int | None = None


# </command>

def _generate_suggestion(error_node, code_text) -> str:
    """
    Generates a suggestion based on the context of the error.
    """
    # Analyze the parent node to provide context
    parent = error_node.parent
    if not parent:
        return "Please check the syntax near the error."

    parent_type = parent.type
    if parent_type == 'content_clause':
        return "Ensure the content block is properly enclosed with matching quotes (''' or \"\")."
    if parent_type == 'update_command':
        return "An action clause ('REPLACE', 'INSERT', 'DELETE') is expected in the 'UPDATE' command."
    if parent_type == 'create_command':
        return "The 'CREATE' command may be missing 'WITH CONTENT' or has a syntax issue."
    # Default suggestion
    return f"Please check the syntax near the error (parent node: {parent_type})"


class _CEDARScriptASTParserBase:
    def __init__(self):
        """Load the CEDARScript language, and initialize the parser.
        """
        self.parser = Parser()
        self.parser.set_language(cedarscript_grammar.language())


class CEDARScriptASTParser(_CEDARScriptASTParserBase):
    def parse_script(self, code_text: str) -> tuple[list[Command], list[ParseError]]:
        """
        Parses the CEDARScript code and returns a tuple containing:
        - A list of Command objects if parsing is successful.
        - A list of ParseError objects if there are parsing errors.
        """
        command_ordinal = 1
        try:
            # Parse the code text
            tree = self.parser.parse(bytes(code_text, 'utf8'))
            root_node = tree.root_node

            errors = self._collect_parse_errors(root_node, code_text, command_ordinal)
            if errors:
                # If there are errors, return them without commands
                return [], errors

            # Extract commands from the parse tree
            commands = []
            for child in root_node.children:
                node_type = child.type.casefold()
                if node_type == 'comment':
                    print("(COMMENT) " + self.parse_string(child).removeprefix("--").strip())
                if not node_type.endswith('_command'):
                    continue
                commands.append(self.parse_command(child))
                command_ordinal += 1

            return commands, []
        except Exception as e:
            # Handle any unexpected exceptions during parsing
            error_message = str(e)
            error = ParseError(
                command_ordinal=command_ordinal,
                message=error_message,
                line=0,
                column=0,
                suggestion="Revise your CEDARScript syntax."
            )
            return [], [error]

    def _collect_parse_errors(self, node, code_text, command_ordinal: int) -> list[ParseError]:
        """
        Recursively traverses the syntax tree to collect parse errors.
        """
        errors = []
        if node.has_error:
            if node.type == 'ERROR':
                # Get the line and column numbers
                start_point = node.start_point  # (row, column)
                line = start_point[0] + 1       # Line numbers start at 1
                column = start_point[1] + 1     # Columns start at 1

                # Extract the erroneous text
                error_text = code_text[node.start_byte:node.end_byte].strip()

                # Create a helpful error message
                message = f"Syntax error near '{error_text}' at line {line}, column {column}."
                suggestion = _generate_suggestion(node, code_text)

                error = ParseError(
                    command_ordinal=command_ordinal,
                    message=message,
                    line=line,
                    column=column,
                    suggestion=suggestion
                )
                errors.append(error)

            # Recurse into children to find all errors
            for child in node.children:
                errors.extend(self._collect_parse_errors(child, code_text, command_ordinal))
        return errors

    def _get_expected_tokens(self, error_node) -> list[str]:
        """
        Provides expected tokens based on the error_node's context.
        """
        # Since Tree-sitter doesn't provide expected tokens directly,
        # you might need to implement this based on the grammar and error context.
        # For now, we'll return an empty list to simplify.
        return []

    def parse_command(self, node):
        match node.type:
            case 'create_command':
                return self.parse_create_command(node)
            case 'rm_file_command':
                return self.parse_rm_file_command(node)
            case 'mv_file_command':
                return self.parse_mv_file_command(node)
            case 'update_command':
                return self.parse_update_command(node)
            # case 'select_command':
            #     return self.parse_select_command(node)
            case _:
                raise ValueError(f"Unexpected command type: {node.type}")

    def parse_create_command(self, node):
        file_path = self.parse_singlefile_clause(self.find_first_by_type(node.children, 'singlefile_clause')).file_path
        content = self.parse_content_clause(self.find_first_by_type(node.children, 'content_clause'))
        return CreateCommand(type='create', file_path=file_path, content=content)

    def parse_rm_file_command(self, node):
        file_path = self.parse_singlefile_clause(self.find_first_by_type(node.children, 'singlefile_clause')).file_path
        return RmFileCommand(type='rm_file', file_path=file_path)

    def parse_mv_file_command(self, node):
        file_path = self.parse_singlefile_clause(self.find_first_by_type(node.children, 'singlefile_clause')).file_path
        target_path = self.parse_to_value_clause(self.find_first_by_type(node.children, 'to_value_clause'))
        return MvFileCommand(type='mv_file', file_path=file_path, target_path=target_path)

    def parse_update_command(self, node):
        target = self.parse_update_target(node)
        action = self.parse_update_action(node)
        content = self.parse_update_content(node)
        return UpdateCommand(type='update', target=target, action=action, content=content)

    def parse_update_target(self, node):
        types = [
            'singlefile_clause',
            'identifier_from_file'
        ]
        target_node = self.find_first_by_type(node.named_children, types)
        if target_node is None:
            raise ValueError("No valid target found in update command")

        match target_node.type.casefold():
            case 'singlefile_clause':
                return self.parse_singlefile_clause(target_node)
            case 'identifier_from_file':
                return self.parse_identifier_from_file(target_node)
            case _ as invalid:
                raise ValueError(f"[parse_update_target] Invalid target: {invalid}")

    def parse_identifier_from_file(self, node):
        identifier_type = node.children[0].type  # FUNCTION, CLASS, or VARIABLE
        file_clause = self.find_first_by_type(node.named_children, 'singlefile_clause')
        where_clause = self.find_first_by_type(node.named_children, 'where_clause')
        offset_clause = self.find_first_by_type(node.named_children, 'offset_clause')

        if not file_clause or not where_clause:
            raise ValueError("Invalid identifier_from_file clause")

        file_path = self.parse_singlefile_clause(file_clause).file_path
        where = self.parse_where_clause(where_clause)
        offset = self.parse_offset_clause(offset_clause) if offset_clause else None

        return IdentifierFromFile(identifier_type=identifier_type, file_path=file_path,
                                  where_clause=where, offset=offset)

    def parse_where_clause(self, node):
        condition = self.find_first_by_type(node.children, 'condition')
        if not condition:
            raise ValueError("No condition found in where clause")

        field = self.parse_string(self.find_first_by_type(condition.children, 'conditions_left'))
        operator = self.parse_string(self.find_first_by_type(condition.children, 'operator'))
        value = self.parse_string(self.find_first_by_type(condition.children, 'string'))

        return WhereClause(field=field, operator=operator, value=value)

    def parse_update_action(self, node):
        child_types = ['update_delete_region_clause', 'update_delete_mos_clause', 'update_move_region_clause', 'update_move_mos_clause',
                                                     'insert_clause', 'replace_mos_clause', 'replace_region_clause']
        action_node = self.find_first_by_type(node.named_children, child_types)
        if action_node is None:
            raise ValueError("No valid action found in update command")

        match action_node.type:
            case 'update_delete_mos_clause' | 'update_delete_region_clause':
                return self.parse_delete_clause(action_node)
            case 'update_move_mos_clause' | 'update_move_region_clause':
                return self.parse_move_clause(action_node)
            case 'insert_clause':
                return self.parse_insert_clause(action_node)
            case 'replace_mos_clause' | 'replace_region_clause':
                return self.parse_replace_clause(action_node)
            case _ as invalid:
                raise ValueError(f'[parse_update_action] Invalid: {invalid}')

    def parse_delete_clause(self, node):
        region = self.parse_region(self.find_first_by_type(node.named_children, ['marker_or_segment', 'region_field']))
        return DeleteClause(region=region)

    def parse_move_clause(self, node):
        source = self.parse_region(self.find_first_by_type(node.named_children, ['marker_or_segment', 'region_field']))
        destination = self.find_first_by_type(node.named_children, 'update_move_clause_destination')
        insert_clause = self.find_first_by_type(destination.named_children, 'insert_clause')
        insert_clause = self.parse_insert_clause(insert_clause)
        rel_indent = self.parse_relative_indentation(self.find_first_by_type(destination.named_children, 'relative_indentation'))
        # TODO to_other_file
        return MoveClause(
            region=source,
            insert_position=insert_clause.insert_position,
            relative_indentation=rel_indent
        )

    def parse_insert_clause(self, node) -> InsertClause:
        relative_marker = self.find_first_by_type(node.children, 'relpos_bai')
        relative_marker: RelativeMarker = self.parse_region(relative_marker)
        # TODO check relative_marker type
        return InsertClause(insert_position=relative_marker)

    def parse_replace_clause(self, node):
        region = self.parse_region(self.find_first_by_type(node.named_children, ['marker_or_segment', 'region_field']))
        return ReplaceClause(region=region)

    def parse_region(self, node) -> Region:
        qualifier = None
        match node.type.casefold():
            case 'marker_or_segment':
                node = node.named_children[0]
            case 'region_field':
                node = node.children[0]
                if node.type.casefold() == 'marker_or_segment':
                    node = node.named_children[0]
            case 'relpos_bai':
                node = node.named_children[0]
                qualifier = RelativePositionType(node.child(0).type.casefold())
                node = node.named_children[0]
            case 'relpos_beforeafter':
                qualifier = RelativePositionType(node.child(0).type.casefold())
                node = node.named_children[0]
            case 'relpos_at':
                node = node.named_children[0]

        match node.type.casefold():
            case 'marker' | 'linemarker':
                result = self.parse_marker(node)
            case 'segment':
                result = self.parse_segment(node)
            case BodyOrWhole.BODY | BodyOrWhole.WHOLE as bow:
                result = BodyOrWhole(bow.lower())
            case _ as invalid:
                raise ValueError(f"[parse_region] Unexpected node type: {invalid}")
        if qualifier:
            result = RelativeMarker(qualifier=qualifier, type=result.type, value=result.value, offset=result.offset)
        return result

    def parse_marker(self, node) -> Marker:
        # TODO Fix: handle line marker as well
        if node.type.casefold() == 'marker':
            node = node.named_children[0]
        marker_type = node.children[0].type  # LINE, VARIABLE, FUNCTION, or CLASS
        value = self.parse_string(self.find_first_by_type(node.named_children, 'string'))
        offset = self.parse_offset_clause(self.find_first_by_type(node.named_children, 'offset_clause'))
        return Marker(type=MarkerType(marker_type.casefold()), value=value, offset=offset)

    def parse_segment(self, node) -> Segment:
        relpos_start = self.find_first_by_type(node.named_children, 'relpos_segment_start').children[1]
        relpos_end = self.find_first_by_type(node.named_children, 'relpos_segment_end').children[1]
        start: RelativeMarker = self.parse_region(relpos_start)
        end: RelativeMarker = self.parse_region(relpos_end)
        return Segment(start=start, end=end)

    def parse_offset_clause(self, node):
        if node is None:
            return None
        return int(self.find_first_by_type(node.children, 'number').text)

    def parse_relative_indentation(self, node):
        if node is None:
            return None
        return int(self.find_first_by_type(node.children, 'number').text)

    def parse_update_content(self, node):
        content_clause = self.find_first_by_type(node.children, 'content_clause')
        if content_clause:
            return self.parse_content_clause(content_clause)
        return None

    def parse_singlefile_clause(self, node):
        if node is None or node.type != 'singlefile_clause':
            raise ValueError("Expected singlefile_clause node")
        path_node = self.find_first_by_type(node.children, 'string')
        if path_node is None:
            raise ValueError("No file_path found in singlefile_clause")
        return SingleFileClause(file_path=self.parse_string(path_node))

    def parse_content_clause(self, node):
        if node is None or node.type != 'content_clause':
            raise ValueError("Expected content_clause node")
        child_type = ['string', 'relative_indent_block', 'multiline_string']
        content_node = self.find_first_by_type(node.children, child_type)
        if content_node is None:
            raise ValueError("No content found in content_clause")
        if content_node.type == 'string':
            return self.parse_string(content_node)
        elif content_node.type == 'relative_indent_block':
            return self.parse_relative_indent_block(content_node)
        elif content_node.type == 'multiline_string':
            return self.parse_multiline_string(content_node)

    def parse_to_value_clause(self, node):
        if node is None or node.type != 'to_value_clause':
            raise ValueError("Expected to_value_clause node")
        value_node = self.find_first_by_type(node.children, 'string')
        if value_node is None:
            raise ValueError("No value found in to_value_clause")
        return self.parse_string(value_node)

    def parse_string(self, node):
        match node.type.casefold():
            case 'string':
                node = node.named_children[0]
        text = node.text.decode('utf8')
        match node.type.casefold():
            case 'raw_string':
                text = text.strip('"\'')
            case 'single_quoted_string':
                text = text.replace("\\'", "'").replace('\\"', '"').strip('"\'')
            case 'multi_line_string':
                text = text.removeprefix("'''").removeprefix('"""').removesuffix("'''").removesuffix('"""')

        return text

    def parse_multiline_string(self, node):
        return node.text.decode('utf8').strip("'''").strip('"""')

    def parse_relative_indent_block(self, node):
        lines = []
        for line_node in node.children:
            if line_node.type == 'relative_indent_line':
                indent_prefix = self.find_first_by_type(line_node.children, 'relative_indent_prefix')
                content = self.find_first_by_type(line_node.children, 'match_any_char')
                if indent_prefix and content:
                    indent = int(indent_prefix.text.strip('@:'))
                    lines.append(f"{' ' * (4 * indent)}{content.text}")
        return '\n'.join(lines)

    def find_first_by_type(self, nodes: list[any], child_type):
        if isinstance(child_type, list):
            for child in nodes:
                if child.type in child_type:
                    return child
        else:
            for child in nodes:
                if child.type == child_type:
                    return child
        return None

    def find_first_by_field_name(self, node: any, field_names):
        if not isinstance(field_names, list):
            return node.child_by_field_name(field_names)

        for field_name in field_names:
            result = node.child_by_field_name(field_name)
            if result:
                return result

        return None

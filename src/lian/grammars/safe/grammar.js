const DIGITS = token(choice('0', seq(/[1-9]/, optional(seq(optional('_'), sep1(/[0-9]+/, /_+/))))));
const DECIMAL_DIGITS = token(sep1(/[0-9]+/, '_'));
const HEX_DIGITS = token(sep1(/[A-Fa-f0-9]+/, '_'));

const PREC = {
  COMMENT: 0,         // //  /*  */
  ASSIGN: 1,          // =  += -=  *=  /=  %=  &=  ^=  |=  <<=  >>=  >>>=
  DECL: 2,
  ELEMENT_VAL: 2,
  TERNARY: 3,         // ?:
  OR: 4,              // ||
  AND: 5,             // &&
  BIT_OR: 6,          // |
  BIT_XOR: 7,         // ^
  BIT_AND: 8,         // &
  EQUALITY: 9,        // ==  !=
  GENERIC: 10,
  REL: 10,            // <  <=  >  >=  instanceof
  SHIFT: 11,          // <<  >>  >>>
  ADD: 12,            // +  -
  MULT: 13,           // *  /  %
  CAST: 14,           // (Type)
  OBJ_INST: 14,       // new
  UNARY: 15,          // ++a  --a  a++  a--  +  -  !  ~
  ARRAY: 16,          // [Index]
  SLICE:16,
  OBJ_ACCESS: 16,     // .
  PARENS: 16,         // (Expression)
  CLASS_LITERAL: 17,  // .
};

module.exports = grammar({
  name: 'safe',

  extras: $ => [
    /\s/,  // Whitespace
    $.line_comment,
    $.block_comment,
  ],

  supertypes: $ => [
    $.statement,
    $.declaration,
    $.type,
    $.comment,
  ],

  inline: $ => [
    $.lvalue,
    $.rvalue,
  ],

  conflicts: $ => [
    [$.expression, $.statement],
    [$.function_declarator, $._variable_declarator_id],
    [$.call_expression, $.primary_expression],
    [$.field_access, $.expression],
    [$.with_statement, $.primary_expression],
    [$.type, $.primary_expression],
    [$.type, $.expression],
    [$._multiline_string_literal, $._string_literal],
    [$.type_identifier, $.primary_expression],
  ],
    
  word: $ => $.identifier,

  rules: {
    program: $ => repeat($._toplevel_statement),
    
    _toplevel_statement: $ => choice(
      $.declaration,
      $.statement,
    ),

    // Literals

    _literal: $ => choice(
      $.decimal_integer_literal,
      $.hex_integer_literal,
      $.octal_integer_literal,
      $.binary_integer_literal,
      $.decimal_floating_point_literal,
      $.hex_floating_point_literal,
      $.true,
      $.false,
      $.character_literal,
      $.string_literal,
      $.null_literal,
    ),

    decimal_integer_literal: _ => token(seq(
      DIGITS,
      optional(choice('l', 'L')),
    )),

    hex_integer_literal: _ => token(seq(
      choice('0x', '0X'),
      HEX_DIGITS,
      optional(choice('l', 'L')),
    )),

    octal_integer_literal: _ => token(seq(
      choice('0o', '0O', '0'),
      sep1(/[0-7]+/, '_'),
      optional(choice('l', 'L')),
    )),

    binary_integer_literal: _ => token(seq(
      choice('0b', '0B'),
      sep1(/[01]+/, '_'),
      optional(choice('l', 'L')),
    )),

    decimal_floating_point_literal: _ => token(choice(
      seq(DECIMAL_DIGITS, '.', optional(DECIMAL_DIGITS), optional(seq((/[eE]/), optional(choice('-', '+')), DECIMAL_DIGITS)), optional(/[fFdD]/)),
      seq('.', DECIMAL_DIGITS, optional(seq((/[eE]/), optional(choice('-', '+')), DECIMAL_DIGITS)), optional(/[fFdD]/)),
      seq(DIGITS, /[eEpP]/, optional(choice('-', '+')), DECIMAL_DIGITS, optional(/[fFdD]/)),
      seq(DIGITS, optional(seq((/[eE]/), optional(choice('-', '+')), DECIMAL_DIGITS)), (/[fFdD]/)),
    )),

    hex_floating_point_literal: _ => token(seq(
      choice('0x', '0X'),
      choice(
        seq(HEX_DIGITS, optional('.')),
        seq(optional(HEX_DIGITS), '.', HEX_DIGITS),
      ),
      optional(seq(
        /[eEpP]/,
        optional(choice('-', '+')),
        DIGITS,
        optional(/[fFdD]/),
      )),
    )),

    true: _ => 'true',

    false: _ => 'false',

    character_literal: _ => token(seq(
      '\'',
      repeat1(choice(
        /[^\\'\n]/,
        /\\./,
        /\\\n/,
      )),
      '\'',
    )),

    string_literal: $ => choice($._string_literal, $._multiline_string_literal),
    _string_literal: $ => seq(
      '"',
      repeat(choice(
        $.string_fragment,
        $.escape_sequence,
        $.string_interpolation,
      )),
      '"',
    ),
    _multiline_string_literal: $ => seq(
      '"',
      repeat(choice(
        alias($._multiline_string_fragment, $.multiline_string_fragment),
        $._escape_sequence,
        $.string_interpolation,
      )),
      '"',
    ),
    // Workaround to https://github.com/tree-sitter/tree-sitter/issues/1156
    // We give names to the token() constructs containing a regexp
    // so as to obtain a node in the CST.

    string_fragment: _ => token.immediate(prec(1, /[^"\\]+/)),
    _multiline_string_fragment: _ => choice(
      /[^"\\]+/,
      seq(/"([^"\\]|\\")*/),
    ),

    string_interpolation: $ => seq(
      '\\{',
      $.expression,
      '}',
    ),

    _escape_sequence: $ => choice(
      prec(2, token.immediate(seq('\\', /[^bfnrts'\"\\]/))),
      prec(1, $.escape_sequence),
    ),
    escape_sequence: _ => token.immediate(seq(
      '\\',
      choice(
        /[^xu0-7]/,
        /[0-7]{1,3}/,
        /x[0-9a-fA-F]{2}/,
        /u[0-9a-fA-F]{4}/,
        /u\{[0-9a-fA-F]+\}/,
      ))),

    null_literal: _ => 'null',

    // Types
    type: $ => choice(
      $.primitive_type,          
      $.tuple_type, 
      $.array_type, 
      $.record_type,           
      $.type_identifier,
    ),

    type_identifier: $ => seq(
      alias($.identifier, $.type_identifier),
      optional(field("type_parameters", $.type_parameters)),

    ),
    
    primitive_type: $ => choice(
      'i8','u8','i16','u16','i32', 'u32', 'i64', 'u64', 'f16','f32', 'f64', 'bool', 'char', 'string'
    ),

    array_type: $ => seq(
      field('data_type', $.type),
      // field('target', $.identifier),
      // '[]', // success
      '[',']', // failed
      // field('dimensions', $.dimensions_expr),
    ),
    
    record_type: $ => seq(
      '{',
      field('key_type', $.type),
      ':',
      field('value_type', $.type),
      '}'
    ),
    //slice
    slice_expression: $ => prec(PREC.SLICE, prec.left(seq(
      field('array', $.identifier),
      '[', 
      seq(
        optional($._slice_argument), // start
        ':', 
        optional($._slice_argument), // end
        optional(seq(':', optional($._slice_argument))) // step
      ),
      ']'
    ))),

    // 切片参数（支持表达式或空）
    _slice_argument: $ => choice(
      $.expression,
      alias($._empty_slice, 'empty') // 处理空参数如 [::2]
    ),

    // 空切片参数处理
    _empty_slice: $ => prec(-1, 
      alias($.empty_token, 'empty') // 使用显式空标记
    ),

    empty_token: $ => token(prec(-1, '')), 

    tuple_type: $ => seq(
      '(',
      commaSep1(field('element_type', $.type)),
      ')'
    ),




    array_index: $ => seq(
      '[',
      field('index', $.int),
      ']'
    ),

    // Declarations
    parameters: $ => commaSep1($.parameter),

    parameter: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $.type)
    ),

    declaration: $ => choice(
      $.local_variable_declaration,
      $.struct_declaration,
      $.union_declaration,
      $.enum_declaration,
      $.function_declaration,
      $.function_signature,
      $.implement_declaration,
      $.trait_declaration,
    ),

    local_variable_declaration: $ => seq(
      optional($.modifiers),
      field('type', $.type),
      $._variable_declarator_list,
      optional(';'),
    ),

    _variable_declarator_list: $ => commaSep1(
      field('declarator', $.variable_declarator),
    ),

    variable_declarator: $ => seq(
      $._variable_declarator_id,
      optional(seq('=', field('value', $._variable_initializer))),
    ),

    _variable_declarator_id: $ => seq(
      field('name', $.identifier),
      // field('dimensions', optional($.dimensions)),
    ),

    _variable_initializer: $ => choice(
      $.expression,
      // $.array_initializer,
    ),

    type_parameters: $ => seq(
      '<', commaSep1($.type_parameter), '>',
    ),

    type_parameter: $ => choice(
      alias($.identifier, $.type_identifier),
      $.constrained_type_parameter,
    ),

    constrained_type_parameter: $ => seq(
      field('left', $.identifier),
      field('bounds', $.trait_bounds),
    ),

    trait_bounds: $ => seq(
      ':',
      alias($.identifier, $.type_identifier),
      repeat(seq(
        field('operator', choice(
          'and',
          'or',
          '||',
          '&&',
        )),
        alias($.identifier, $.type_identifier),
      )),
    ),

    union_declaration: $ => seq(
      'union',
      field('name', $.identifier),
      optional(field("type_parameters", $.type_parameters)),
      '{',
      repeat($.declaration),
      '}',
    ),

    enum_declaration: $ => prec.right(seq(
      'enum',
      choice(
        seq(
          field('name', $.identifier),
          optional(seq(':', field('underlying_type', $.type))),
          optional(field('body', $.enumerator_list)),
        ),
        field('body', $.enumerator_list),
      ),
    )),

    enumerator: $ => seq(
      field('name', $.identifier),
      optional(seq('=', field('value', $.expression))),
    ),

    enumerator_list: $ => seq(
      '{',
      commaSep1($.enumerator),
      '}',
    ),

    struct_declaration: $ => choice(
      $.original_struct,
      $.tuple_struct,
    ),

    original_struct: $ => seq(
      'struct',
      field('name', $.identifier),
      optional(field("type_parameters", $.type_parameters)),
      '{',
      repeat($.declaration),
      '}',
    ),

    tuple_struct: $ => seq(
      'struct',
      field('name', $.identifier),
      '(',
      commaSep1($.type),
      ')',
    ),

    function_declaration: $ => seq(
      $.function_header,
      $.function_body,
    ),
    function_signature: $ => seq(
      $.function_header,
      ';',
    ),

    function_header: $ => seq(
      field('type', $.type),
      $.function_declarator,
    ),

    function_declarator: $ => seq(
      field('name', $.identifier),
      optional(field('type_parameters', $.type_parameters)),
      field('parameters', $.formal_parameters),
      // field('dimensions', optional($.dimensions)),
    ),

    formal_parameters: $ => seq(
      '(',
          commaSep($.formal_parameter),
      ')',
    ),

    formal_parameter: $ => seq(
      optional($.modifiers),
      field('type', $.type),
      $._variable_declarator_id,
    ),

    function_body: $ => seq(
      '{',
      repeat($.declaration),  
      repeat($.statement),    
      '}',
    ),
    function_name: $ => choice(
      $.identifier,
    ),
    
    file_location: $ => token(/[^>]+/),

    implement_declaration: $ => seq(
      'impl',
      field('name', $.identifier),
      optional(field("type_parameters", $.type_parameters)),
      field("implement_body", $.implement_body),
    ),

    implement_body: $ => choice(
      seq(
        '{',
        repeat($.function_declaration),
        '}',
      ),
      seq(
        ':',
        field('trait_type', $.trait_list),
        choice(
          ';',
          seq(
            '{',
            repeat($.function_declaration),
            '}',
          ),
        ),
      ),
    ),

    trait_list: $ => commaSep1(alias($.identifier, $.type_identifier)),

    trait_declaration: $ => prec.right(seq(
      'trait',
      field('name', $.identifier),
      optional(field("type_parameters", $.type_parameters)),
      optional(seq(
        '{',
        repeat(choice(
          $.function_declaration,
          $.function_signature,
        )),
        '}',
      )),
    )),

    // Statements
    statement: $ =>choice(
      $.expression_statement,
      $.if_statement,
      $.ok_statement,
      $.while_statement,
      $.for_statement,
      $.infiloop_statement,
      $.label_statement,
      $.goto_statement,
      $.switch_statement,
      $.with_statement,
      $.block,
      $.return_statement,
    ),

    if_statement: $ => prec.right(seq(
      'if',
      field('condition', $.expression),
      field('consequence', $.statement),
      repeat(field('alternative', $.elif_clause)),
      optional(field('alternative', $.else_clause)),
    )),

    ok_statement: $ => prec.right(seq(
      'Ok',
      field('condition', $.expression),
      field('consequence', $.statement),
      optional(field('alternative', $.else_clause)),
    )),

    elif_clause: $ => seq(
      'elif',
      field('condition', $.expression),
      field('consequence', $.statement),
    ),

    else_clause: $ => seq(
      'else',
      field('consequence', $.statement),
    ), 

    while_statement: $ => seq(
      'while',
      field('condition', $.expression),
      field('body', $.statement),
    ),

    for_statement: $ => seq(
      'for',
      choice(
        field('init', $.local_variable_declaration),
        seq(
          commaSep(field('init', $.expression)),
          ';',
        ),
      ),
      field('condition', $.expression),
      field('update', $.statement),
      field('body', $.statement),
    ),

    infiloop_statement: $ => seq(
      'loop',
      field('body', $.statement),
    ),

    block: $ => seq(
      '{', repeat($.statement), '}',
    ),

    label_statement: $ => seq(
      'label_stmt',
      field('label_name', $.identifier),
    ),

    goto_statement: $ => seq(
      'goto_stmt',
      field('label_name', $.identifier),
    ),

    switch_statement: $ => seq(
      'switch',
      field('condition', $.expression),
      field('body', $.switch_block),
    ),

    switch_block: $ => seq(
      '{',
      repeat($.switch_block_statement_group),
      '}',
    ),

    switch_block_statement_group: $ => prec.left(seq(
      repeat1(seq($.switch_label, ':')),
      repeat($.statement),
    )),

    switch_label: $ => choice(
      seq('case',
        commaSep1(choice(
          $.type,
          $.expression,
        )),
      ),
      'default',
    ),

    with_statement: $ => seq(
      'with',
      field('receiver', $.field_access),
      field('body', $.statement),
    ),

    return_statement: $ => prec.right(seq(
      'return',
      optional($.expression),
    )),

    expression_statement: $ => seq(
      $.expression,
    ),

    expression: $ => choice(
      $.assignment_expression,
      $.binary_expression,
      $.slice_expression,
      $.unary_expression,
      $.self,
      $.primary_expression,
      // $.object_creation_expression,
    ),

    primary_expression: $ => choice(
      $._literal,
      $.identifier,
      $.field_access,
      $.array_access,
      $.call_expression,
    ),

    // object_creation_expression: $ => seq(
    //   field("data_type", $.type_identifier),
    // ),

    self: $ => 'self',

    call_expression: $ =>  seq(
      field('function_name', $.identifier),
      $.argument_list,
    ),

    argument_list: $ => seq('(', commaSep($.expression), ')'),

    dimensions_expr: $ => seq('[', commaSep($.expression), ']'),

    assignment_expression: $ => prec.right(PREC.ASSIGN, seq(
      field('left', choice(
        $.identifier,
        $.field_access,
        $.array_access,
      )),
      field('operator', choice('=', '+=', '-=', '*=', '/=', '&=', '|=', '^=')),
      field('right', $.expression),
    )),

    field_access: $ => seq(
      field('object', choice($.primary_expression, $.self)),
      '.',
      field('field', choice($.identifier, $.int)),
    ),
    
    array_access: $ => seq(
      field('array', $.identifier),
      '[',
      $.dimensions_expr,
      ']',
    ),

    binary_expression: $ => choice(
      ...[
        ['>', PREC.REL],
        ['<', PREC.REL],
        ['>=', PREC.REL],
        ['<=', PREC.REL],
        ['==', PREC.EQUALITY],
        ['!=', PREC.EQUALITY],
        ['&&', PREC.AND],
        ['||', PREC.OR],
        ['+', PREC.ADD],
        ['-', PREC.ADD],
        ['*', PREC.MULT],
        ['/', PREC.MULT],
        ['&', PREC.BIT_AND],
        ['|', PREC.BIT_OR],
        ['^', PREC.BIT_XOR],
        ['%', PREC.MULT],
        ['<<', PREC.SHIFT],
        ['>>', PREC.SHIFT],
        ['>>>', PREC.SHIFT],
      ].map(([operator, precedence]) =>
        prec.left(precedence, seq(
          field('left', $.expression),
          // @ts-ignore
          field('operator', operator),
          field('right', $.expression),
        )),
      )),

      unary_expression: $ => choice(...[
        ['+', PREC.UNARY],
        ['-', PREC.UNARY],
        ['!', PREC.UNARY],
        ['~', PREC.UNARY],
      ].map(([operator, precedence]) =>
        prec.left(precedence, seq(
          // @ts-ignore
          field('operator', operator),
          field('operand', $.expression),
        )),
      )),
    
    modifiers: $ => choice(
      'local',
      'static',
      'shared',
      'const',
      'public',
      'private',
    ),




    parenthesized_expression: $ => prec.left(PREC.PARENS, seq(
      '(',
      field('expression', $.expression),  
      ')'
    )),
    
    // Constants
    constant: $ => choice(
      $.int,                       
      $.uint,                      
      $.float,                    
      $.bool,                      
      $.bytes,                    
      $.static_string,                      
      seq('(', commaSep($.constant), ')'),   // (CONSTANT...)
      seq('[', commaSep($.constant), ']')    // [CONSTANT...]
    ),

    // Data Types
    region: $ => token(seq("'", /[_a-zA-Z][_a-zA-Z0-9]*/)),

    lifetime: $ => token(seq("'", /[_a-zA-Z][_a-zA-Z0-9]*/)),
    
    identifier: $ => /[_a-zA-Z][_a-zA-Z0-9]*/,

    int: $ => /\d+/,

    uint: $ => /\d+u\d*/,

    float: $ => /\d+\.\d+/,

    bool: $ => choice('true', 'false'),

    bytes: $ => /b"[^"\\]*(?:\\.[^"\\]*)*"/,

    static_string: $ => /"[^"\\]*(?:\\.[^"\\]*)*"/,

    item_with_substs: $ => seq(
      field('identifier', $.identifier),
      '<',
      commaSep(field('substitution', $.type)),  
      '>'
    ),

    trait_projection: $ => seq(
      '<',
      field('parameter', $.identifier),  // P0
      'as',
      field('trait', $.identifier),      // TRAIT
      '<',
      commaSep(field('generic_arg', $.type)),   // P1...Pn
      '>',
      '>'
    ),


    comment: $ => choice(
      $.line_comment,
      $.block_comment,
    ),

    line_comment: _ => token(prec(PREC.COMMENT, seq('//', /.*/))),
    
    block_comment: _ => token(prec(PREC.COMMENT,
      seq('/*', /[^*]*\*+([^/*][^*]*\*+)*/, '/')
    )),
  },
});

/**
 * Creates a rule to match one or more of the rules separated by separator
 *
 * @param {RuleOrLiteral} rule
 *
 * @param {RuleOrLiteral} separator
 *
 * @return {SeqRule}
 *
 */
function sep1(rule, separator) {
  return seq(rule, repeat(seq(separator, rule)));
}

/**
 * Creates a rule to match one or more of the rules separated by a comma
 *
 * @param {RuleOrLiteral} rule
 *
 * @return {SeqRule}
 *
 */
function commaSep1(rule) {
  return sep1(rule, ',');
}

/**
 * Creates a rule to optionally match one or more of the rules separated by a comma
 *
 * @param {RuleOrLiteral} rule
 *
 * @return {ChoiceRule}
 *
 */
function commaSep(rule) {
  return optional(commaSep1(rule));
}


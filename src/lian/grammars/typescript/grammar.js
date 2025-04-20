module.exports = grammar({
    name: 'typescript',
  
    extras: $ => [
      $.comment,
      /[\s\p{Zs}\uFEFF\u2028\u2029\u2060\u200B]/,
    ],
  
    supertypes: $ => [
      $.statement,
      $.declaration,
      $.expression,
      $.primary_expression,
      $.pattern,
      $._primary_type,
    ],
  
    inline: $ => [
      $.statement,
      $._expressions,
      $._semicolon,
      $._identifier,
      $._reserved_identifier,
      $._jsx_attribute,
      $._jsx_element_name,
      $._jsx_child,
      $._jsx_element,
      $._jsx_attribute_name,
      $._jsx_attribute_value,
      $._jsx_identifier,
      $._lhs_expression,
      $._type_identifier,
      $._jsx_start_opening_element,
    ],
  
    precedences: $ => [
      [
        'member',
        'call',
        $.update_expression,
        'unary_void',
        'binary_exp',
        'binary_times',
        'binary_plus',
        'binary_shift',
        'binary_compare',
        'binary_relation',
        'binary_equality',
        'bitwise_and',
        'bitwise_xor',
        'bitwise_or',
        'logical_and',
        'logical_or',
        'ternary',
        $.sequence_expression,
        $.arrow_function,
      ],
      ['assign', $.primary_expression],
      ['member', 'new', 'call', $.expression],
      ['declaration', 'literal'],
      [$.primary_expression, $.statement_block, 'object'],
      [$.import_statement, $.import],
      [$.export_statement, $.primary_expression],
      [$.lexical_declaration, $.primary_expression],
      [
        'call',
        'instantiation',
        'unary',
        'binary',
        $.await_expression,
        $.arrow_function,
      ],
      [
        'extends',
        'instantiation',
      ],
      [
        $.intersection_type,
        $.union_type,
        $.conditional_type,
        $.function_type,
        'binary',
        $.type_predicate,
        $.readonly_type,
      ],
      [$.mapped_type_clause, $.primary_expression],
      [$.accessibility_modifier, $.primary_expression],
      ['unary_void', $.expression],
      [$.extends_clause, $.primary_expression],
      ['unary', 'assign'],
      ['declaration', $.expression],
      [$.predefined_type, $.unary_expression],
      [$._type, $.flow_maybe_type],
      [$.tuple_type, $.array_type, $.pattern, $._type],
      [$.readonly_type, $.pattern],
      [$.readonly_type, $.primary_expression],
      [$.type_query, $.subscript_expression, $.expression],
      [$.type_query, $._type_query_subscript_expression],
      [$.nested_type_identifier, $.generic_type, $._primary_type, $.lookup_type, $.index_type_query, $._type],
      [$.as_expression, $.satisfies_expression, $._primary_type],
      [$._type_query_member_expression, $.member_expression],
      [$.member_expression, $._type_query_member_expression_in_type_annotation],
      [$._type_query_member_expression, $.primary_expression],
      [$._type_query_subscript_expression, $.subscript_expression],
      [$._type_query_subscript_expression, $.primary_expression],
      [$._type_query_call_expression, $.primary_expression],
      [$._type_query_instantiation_expression, $.primary_expression],
      [$.type_query, $.primary_expression],
      [$.override_modifier, $.primary_expression],
      [$.decorator_call_expression, $.decorator],
      [$.literal_type, $.pattern],
      [$.predefined_type, $.pattern],
      [$.call_expression, $._type_query_call_expression],
      [$.call_expression, $._type_query_call_expression_in_type_annotation],
      [$.new_expression, $.primary_expression],
      [$.meta_property, $.primary_expression],
      [$.construct_signature, $._property_name],
    ],
  
    conflicts: $ => [
      [$.primary_expression, $._property_name],
      [$.primary_expression, $._property_name, $.arrow_function],
      [$.primary_expression, $.arrow_function],
      [$.primary_expression, $.method_definition],
      [$.primary_expression, $.rest_pattern],
      [$.primary_expression, $.pattern],
      [$.primary_expression, $._for_header],
      [$.array, $.array_pattern],
      [$.object, $.object_pattern],
      [$.assignment_expression, $.pattern],
      [$.assignment_expression, $.object_assignment_pattern],
      [$.labeled_statement, $._property_name],
      [$.computed_property_name, $.array],
      [$.binary_expression, $._initializer],
  
      [$.call_expression, $.instantiation_expression, $.binary_expression],
      [$.call_expression, $.instantiation_expression, $.binary_expression, $.unary_expression],
      [$.call_expression, $.instantiation_expression, $.binary_expression, $.update_expression],
      [$.call_expression, $.instantiation_expression, $.binary_expression, $.await_expression],
  
      [$.class],
  
      [$.nested_identifier, $.nested_type_identifier, $.primary_expression],
      [$.nested_identifier, $.nested_type_identifier],
  
      [$._call_signature, $.function_type],
      [$._call_signature, $.constructor_type],
  
      [$._primary_type, $.type_parameter],
  
      [$.primary_expression, $._parameter_name],
      [$.primary_expression, $._parameter_name, $._primary_type],
      [$.primary_expression, $.literal_type],
      [$.primary_expression, $.literal_type, $.rest_pattern],
      [$.primary_expression, $.predefined_type, $.rest_pattern],
      [$.primary_expression, $._primary_type],
      [$.primary_expression, $.generic_type],
      [$.primary_expression, $.predefined_type],
      [$.primary_expression, $.pattern, $._primary_type],
      [$._parameter_name, $._primary_type],
      [$.pattern, $._primary_type],
  
      [$.optional_tuple_parameter, $._primary_type],
      [$.optional_tuple_parameter, $._primary_type, $.primary_expression],
      [$.rest_pattern, $._primary_type, $.primary_expression],
  
      [$.object, $.object_type],
      [$.object, $.object_pattern, $.object_type],
      [$.object, $.object_pattern, $._property_name],
      [$.object_pattern, $.object_type],
      [$.object_pattern, $.object_type],
  
      [$.array, $.tuple_type],
      [$.array, $.array_pattern, $.tuple_type],
      [$.array_pattern, $.tuple_type],
  
      [$.template_literal_type, $.template_string],
    ],
  
    word: $ => $.identifier,
  
    rules: {
      program: $ => seq(
        optional($.hash_bang_line),
        repeat($.statement),
      ),
  
      hash_bang_line: _ => /#!.*/,
  
      export_statement: $ => choice(
        seq(
          'export',
          choice(
            seq('*', $._from_clause),
            seq($.namespace_export, $._from_clause),
            seq($.export_clause, $._from_clause),
            $.export_clause,
          ),
          $._semicolon,
        ),
        seq(
          repeat(field('decorator', $.decorator)),
          'export',
          choice(
            field('declaration', $.declaration),
            seq(
              'default',
              choice(
                field('declaration', $.declaration),
                seq(
                  field('value', $.expression),
                  $._semicolon,
                ),
              ),
            ),
          ),
        ),
        seq(
          'export',
          'type',
          $.export_clause,
          optional($._from_clause),
          $._semicolon,
        ),
        seq('export', '=', $.expression, $._semicolon),
        seq('export', 'as', 'namespace', $.identifier, $._semicolon),
      ),
  
      namespace_export: $ => seq(
        '*', 'as', $._module_export_name,
      ),
  
      export_clause: $ => seq(
        '{',
        commaSep($.export_specifier),
        optional(','),
        '}',
      ),
  
      export_specifier: $ => seq(
        field('name', $._module_export_name),
        optional(seq(
          'as',
          field('alias', $._module_export_name),
        )),
      ),
  
      _module_export_name: $ => choice(
        $.identifier,
        $.string,
      ),
  
      declaration: $ => choice(
        $.function_declaration,
        $.generator_function_declaration,
        $.class_declaration,
        $.lexical_declaration,
        $.variable_declaration,
        $.function_signature,
        $.abstract_class_declaration,
        $.module,
        prec('declaration', $.internal_module),
        $.type_alias_declaration,
        $.enum_declaration,
        $.interface_declaration,
        $.import_alias,
        $.ambient_declaration,
      ),
  
      import: _ => token('import'),
  
      _import_identifier: $ => choice($.identifier, alias('type', $.identifier)),
  
      import_statement: $ => seq(
        'import',
        optional(choice('type', 'typeof')),
        choice(
          seq($.import_clause, $._from_clause),
          $.import_require_clause,
          field('source', $.string),
        ),
        optional($.import_attribute),
        $._semicolon,
      ),
  
      import_clause: $ => choice(
        $.namespace_import,
        $.named_imports,
        seq(
          $._import_identifier,
          optional(seq(
            ',',
            choice(
              $.namespace_import,
              $.named_imports,
            ),
          )),
        ),
      ),
  
      import_require_clause: $ => seq(
        $.identifier,
        '=',
        'require',
        '(',
        field('source', $.string),
        ')',
      ),
  
      _from_clause: $ => seq(
        'from', field('source', $.string),
      ),
  
      namespace_import: $ => seq(
        '*', 'as', $.identifier,
      ),
  
      named_imports: $ => seq(
        '{',
        commaSep($.import_specifier),
        optional(','),
        '}',
      ),
  
      import_specifier: $ => seq(
        optional(choice('type', 'typeof')),
        choice(
          field('name', $._import_identifier),
          seq(
            field('name', choice($._module_export_name, alias('type', $.identifier))),
            'as',
            field('alias', $._import_identifier),
          ),
        )
      ),
  
      import_attribute: $ => seq('with', $.object),
  
      statement: $ => choice(
        $.export_statement,
        $.import_statement,
        $.debugger_statement,
        $.expression_statement,
        $.declaration,
        $.statement_block,
  
        $.if_statement,
        $.switch_statement,
        $.for_statement,
        $.for_in_statement,
        $.while_statement,
        $.do_statement,
        $.try_statement,
        $.with_statement,
  
        $.break_statement,
        $.continue_statement,
        $.return_statement,
        $.throw_statement,
        $.empty_statement,
        $.labeled_statement,
      ),
  
      expression_statement: $ => seq(
        $._expressions,
        $._semicolon,
      ),
  
      variable_declaration: $ => seq(
        'var',
        commaSep1($.variable_declarator),
        $._semicolon,
      ),
  
      lexical_declaration: $ => seq(
        field('kind', choice('let', 'const')),
        commaSep1($.variable_declarator),
        $._semicolon,
      ),
  
      variable_declarator: $ => choice(
        seq(
          field('name', choice($.identifier, $._destructuring_pattern)),
          field('type', optional($.type_annotation)),
          optional($._initializer),
        ),
        prec('declaration', seq(
          field('name', $.identifier),
          '!',
          field('type', $.type_annotation),
        )),
      ),
  
      statement_block: $ => prec.right(seq(
        '{',
        repeat($.statement),
        '}',
        optional($._semicolon),
      )),
  
      else_clause: $ => seq('else', $.statement),
  
      if_statement: $ => prec.right(seq(
        'if',
        field('condition', $.parenthesized_expression),
        field('consequence', $.statement),
        optional(field('alternative', $.else_clause)),
      )),
  
      switch_statement: $ => seq(
        'switch',
        field('value', $.parenthesized_expression),
        field('body', $.switch_body),
      ),
  
      for_statement: $ => seq(
        'for',
        '(',
        field('initializer', choice(
          $.lexical_declaration,
          $.variable_declaration,
          $.expression_statement,
          $.empty_statement,
        )),
        field('condition', choice(
          $.expression_statement,
          $.empty_statement,
        )),
        field('increment', optional($._expressions)),
        ')',
        field('body', $.statement),
      ),
  
      for_in_statement: $ => seq(
        'for',
        optional('await'),
        $._for_header,
        field('body', $.statement),
      ),
  
      _for_header: $ => seq(
        '(',
        choice(
          field('left', choice(
            $._lhs_expression,
            $.parenthesized_expression,
          )),
          seq(
            field('kind', 'var'),
            field('left', choice(
              $.identifier,
              $._destructuring_pattern,
            )),
            optional($._initializer),
          ),
          seq(
            field('kind', choice('let', 'const')),
            field('left', choice(
              $.identifier,
              $._destructuring_pattern,
            )),
          ),
        ),
        field('operator', choice('in', 'of')),
        field('right', $._expressions),
        ')',
      ),
  
      while_statement: $ => seq(
        'while',
        field('condition', $.parenthesized_expression),
        field('body', $.statement),
      ),
  
      do_statement: $ => prec.right(seq(
        'do',
        field('body', $.statement),
        'while',
        field('condition', $.parenthesized_expression),
        optional($._semicolon),
      )),
  
      try_statement: $ => seq(
        'try',
        field('body', $.statement_block),
        optional(field('handler', $.catch_clause)),
        optional(field('finalizer', $.finally_clause)),
      ),
  
      with_statement: $ => seq(
        'with',
        field('object', $.parenthesized_expression),
        field('body', $.statement),
      ),
  
      break_statement: $ => seq(
        'break',
        field('label', optional(alias($.identifier, $.statement_identifier))),
        $._semicolon,
      ),
  
      continue_statement: $ => seq(
        'continue',
        field('label', optional(alias($.identifier, $.statement_identifier))),
        $._semicolon,
      ),
  
      debugger_statement: $ => seq(
        'debugger',
        $._semicolon,
      ),
  
      return_statement: $ => seq(
        'return',
        optional($._expressions),
        $._semicolon,
      ),
  
      throw_statement: $ => seq(
        'throw',
        $._expressions,
        $._semicolon,
      ),
  
      empty_statement: _ => ';',
  
      labeled_statement: $ => prec.dynamic(-1, seq(
        field('label', alias(choice($.identifier, $._reserved_identifier), $.statement_identifier)),
        ':',
        field('body', $.statement),
      )),
  
      switch_body: $ => seq(
        '{',
        repeat(choice($.switch_case, $.switch_default)),
        '}',
      ),
  
      switch_case: $ => seq(
        'case',
        field('value', $._expressions),
        ':',
        field('body', repeat($.statement)),
      ),
  
      switch_default: $ => seq(
        'default',
        ':',
        field('body', repeat($.statement)),
      ),
  
      catch_clause: $ => seq(
        'catch',
        optional(
          seq(
            '(',
            field(
              'parameter',
              choice($.identifier, $._destructuring_pattern),
            ),
            optional(
              field('type', $.type_annotation),
            ),
            ')',
          ),
        ),
        field('body', $.statement_block),
      ),
  
      finally_clause: $ => seq(
        'finally',
        field('body', $.statement_block),
      ),
  
      parenthesized_expression: $ => seq(
        '(',
        choice(
          seq($.expression, field('type', optional($.type_annotation))),
          $.sequence_expression,
        ),
        ')',
      ),
  
      _expressions: $ => choice(
        $.expression,
        $.sequence_expression,
      ),
  
      expression: $ => choice(
        $.primary_expression,
        $.glimmer_template,
        $.assignment_expression,
        $.augmented_assignment_expression,
        $.await_expression,
        $.unary_expression,
        $.binary_expression,
        $.ternary_expression,
        $.update_expression,
        $.new_expression,
        $.yield_expression,
        $.as_expression,
        $.satisfies_expression,
        $.instantiation_expression,
        $.internal_module,
        $.type_assertion
      ),
  
      primary_expression: $ => choice(
        $.subscript_expression,
        $.member_expression,
        $.parenthesized_expression,
        $._identifier,
        alias($._reserved_identifier, $.identifier),
        $.this,
        $.super,
        $.number,
        $.string,
        $.template_string,
        $.regex,
        $.true,
        $.false,
        $.null,
        $.object,
        $.array,
        $.function_expression,
        $.arrow_function,
        $.generator_function,
        $.class,
        $.meta_property,
        $.call_expression,
        $.non_null_expression,
      ),
  
      yield_expression: $ => prec.right(seq(
        'yield',
        choice(
          seq('*', $.expression),
          optional($.expression),
        ))),
  
      object: $ => prec('object', seq(
        '{',
        commaSep(optional(choice(
          $.pair,
          $.spread_element,
          $.method_definition,
          alias(
            choice($.identifier, $._reserved_identifier),
            $.shorthand_property_identifier,
          ),
        ))),
        '}',
      )),
  
      object_pattern: $ => prec('object', seq(
        '{',
        commaSep(optional(choice(
          $.pair_pattern,
          $.rest_pattern,
          $.object_assignment_pattern,
          alias(
            choice($.identifier, $._reserved_identifier),
            $.shorthand_property_identifier_pattern,
          ),
        ))),
        '}',
      )),
  
      assignment_pattern: $ => seq(
        field('left', $.pattern),
        '=',
        field('right', $.expression),
      ),
  
      object_assignment_pattern: $ => seq(
        field('left', choice(
          alias(choice($._reserved_identifier, $.identifier), $.shorthand_property_identifier_pattern),
          $._destructuring_pattern,
        )),
        '=',
        field('right', $.expression),
      ),
  
      array: $ => seq(
        '[',
        commaSep(optional(choice(
          $.expression,
          $.spread_element,
        ))),
        ']',
      ),
  
      array_pattern: $ => seq(
        '[',
        commaSep(optional(choice(
          $.pattern,
          $.assignment_pattern,
        ))),
        ']',
      ),
  
      glimmer_template: $ => choice(
        seq(
          field('open_tag', $.glimmer_opening_tag),
          field('content', repeat($._glimmer_template_content)),
          field('close_tag', $.glimmer_closing_tag),
        ),
        seq(
          field('open_tag', $.glimmer_opening_tag),
          field('close_tag', $.glimmer_closing_tag),
        ),
      ),
  
      _glimmer_template_content: _ => /.{1,}/,
      glimmer_opening_tag: _ => seq('<template>'),
      glimmer_closing_tag: _ => seq('</template>'),
  
      _jsx_element: $ => choice($.jsx_element, $.jsx_self_closing_element),
  
      jsx_element: $ => seq(
        field('open_tag', $.jsx_opening_element),
        repeat($._jsx_child),
        field('close_tag', $.jsx_closing_element),
      ),
  
      jsx_text: _ => choice(
        /[^{}<>\n& ]([^{}<>\n&]*[^{}<>\n& ])?/,
        /\/\/[^\n]*/,
      ),
  
      html_character_reference: _ => /&(#([xX][0-9a-fA-F]{1,6}|[0-9]{1,5})|[A-Za-z]{1,30});/,
  
      jsx_expression: $ => seq(
        '{',
        optional(choice(
          $.expression,
          $.sequence_expression,
          $.spread_element,
        )),
        '}',
      ),
  
      _jsx_child: $ => choice(
        $.jsx_text,
        $.html_character_reference,
        $._jsx_element,
        $.jsx_expression,
      ),
  
      jsx_opening_element: $ => prec.dynamic(-1, seq(
        '<',
        optional(seq(
          field('name', $._jsx_element_name),
          repeat(field('attribute', $._jsx_attribute)),
        )),
        '>',
      )),
  
      jsx_identifier: _ => /[a-zA-Z_$][a-zA-Z\d_$]*-[a-zA-Z\d_$\-]*/,
  
      _jsx_identifier: $ => choice(
        alias($.jsx_identifier, $.identifier),
        $.identifier,
      ),
  
      nested_identifier: $ => prec('member', seq(
        field('object', choice($.identifier, alias($.nested_identifier, $.member_expression))),
        '.',
        field('property', alias($.identifier, $.property_identifier)),
      )),
  
      jsx_namespace_name: $ => seq($._jsx_identifier, ':', $._jsx_identifier),
  
      _jsx_element_name: $ => choice(
        $._jsx_identifier,
        alias($.nested_identifier, $.member_expression),
        $.jsx_namespace_name,
      ),
  
      jsx_closing_element: $ => seq(
        '</',
        optional(field('name', $._jsx_element_name)),
        '>',
      ),
  
      jsx_self_closing_element: $ => seq(
        '<',
        field('name', $._jsx_element_name),
        repeat(field('attribute', $._jsx_attribute)),
        '/>',
      ),
  
      _jsx_attribute: $ => choice($.jsx_attribute, $.jsx_expression),
  
      _jsx_attribute_name: $ => choice(alias($._jsx_identifier, $.property_identifier), $.jsx_namespace_name),
  
      jsx_attribute: $ => seq(
        $._jsx_attribute_name,
        optional(seq(
          '=',
          $._jsx_attribute_value,
        )),
      ),
  
      _jsx_string: $ => choice(
        seq(
          '"',
          repeat(choice(
            alias($.unescaped_double_jsx_string_fragment, $.string_fragment),
            $.html_character_reference,
          )),
          '"',
        ),
        seq(
          '\'',
          repeat(choice(
            alias($.unescaped_single_jsx_string_fragment, $.string_fragment),
            $.html_character_reference,
          )),
          '\'',
        ),
      ),
  
      unescaped_double_jsx_string_fragment: _ => token.immediate(prec(1, /([^"&]|&[^#A-Za-z])+/)),
  
      unescaped_single_jsx_string_fragment: _ => token.immediate(prec(1, /([^'&]|&[^#A-Za-z])+/)),
  
      _jsx_attribute_value: $ => choice(
        alias($._jsx_string, $.string),
        $.jsx_expression,
        $._jsx_element,
      ),
  
      class: $ => prec('literal', seq(
        repeat(field('decorator', $.decorator)),
        'class',
        field('name', optional($._type_identifier)),
        field('type_parameters', optional($.type_parameters)),
        optional($.class_heritage),
        field('body', $.class_body),
      )),
  
      abstract_class_declaration: $ => prec('declaration', seq(
        repeat(field('decorator', $.decorator)),
        'abstract',
        'class',
        field('name', $._type_identifier),
        field('type_parameters', optional($.type_parameters)),
        optional($.class_heritage),
        field('body', $.class_body),
      )),
  
      class_declaration: $ => prec.left('declaration', seq(
        repeat(field('decorator', $.decorator)),
        'class',
        field('name', $._type_identifier),
        field('type_parameters', optional($.type_parameters)),
        optional($.class_heritage),
        field('body', $.class_body),
        optional($._semicolon),
      )),
  
      class_heritage: $ => choice(
        seq($.extends_clause, optional($.implements_clause)),
        $.implements_clause,
      ),
  
      function_expression: $ => prec('literal', seq(
        optional('async'),
        'function',
        field('name', optional($.identifier)),
        $._call_signature,
        field('body', $.statement_block),
      )),
  
      function_declaration: $ => prec.right('declaration', seq(
        optional('async'),
        'function',
        field('name', $.identifier),
        $._call_signature,
        field('body', $.statement_block),
        optional($._semicolon),
      )),
  
      generator_function: $ => prec('literal', seq(
        optional('async'),
        'function',
        '*',
        field('name', optional($.identifier)),
        $._call_signature,
        field('body', $.statement_block),
      )),
  
      generator_function_declaration: $ => prec.right('declaration', seq(
        optional('async'),
        'function',
        '*',
        field('name', $.identifier),
        $._call_signature,
        field('body', $.statement_block),
        optional($._semicolon),
      )),
  
      arrow_function: $ => seq(
        optional('async'),
        choice(
          field('parameter', choice(
            alias($._reserved_identifier, $.identifier),
            $.identifier,
          )),
          $._call_signature,
        ),
        '=>',
        field('body', choice(
          $.expression,
          $.statement_block,
        )),
      ),
  
      call_signature: $ => $._call_signature,
      _call_signature: $ => seq(
        field('type_parameters', optional($.type_parameters)),
        field('parameters', $.formal_parameters),
        field('return_type', optional(
          choice($.type_annotation, $.asserts_annotation, $.type_predicate_annotation),
        )),
      ),
  
      _formal_parameter: $ => choice(
        $.required_parameter,
        $.optional_parameter,
      ),
  
      optional_chain: _ => '?.',
  
      call_expression: $ => choice(
        prec('call', seq(
          field('function', choice($.expression, $.import)),
          field('type_arguments', optional($.type_arguments)),
          field('arguments', choice($.arguments, $.template_string)),
        )),
        prec('member', seq(
          field('function', $.primary_expression),
          '?.',
          field('type_arguments', optional($.type_arguments)),
          field('arguments', $.arguments),
        )),
      ),
  
      new_expression: $ => prec.right('new', seq(
        'new',
        field('constructor', $.primary_expression),
        field('type_arguments', optional($.type_arguments)),
        field('arguments', optional($.arguments)),
      )),
  
      await_expression: $ => prec('unary_void', seq(
        'await',
        $.expression,
      )),
  
      member_expression: $ => prec('member', seq(
        field('object', choice($.expression, $.primary_expression, $.import)),
        choice('.', field('optional_chain', $.optional_chain)),
        field('property', choice(
          $.private_property_identifier,
          alias($.identifier, $.property_identifier))),
      )),
  
      subscript_expression: $ => prec.right('member', seq(
        field('object', choice($.expression, $.primary_expression)),
        optional(field('optional_chain', $.optional_chain)),
        '[', field('index', $._expressions), ']',
      )),
  
      _lhs_expression: $ => choice(
        $.member_expression,
        $.subscript_expression,
        $._identifier,
        alias($._reserved_identifier, $.identifier),
        $._destructuring_pattern,
        $.non_null_expression
      ),
  
      assignment_expression: $ => prec.right('assign', seq(
        optional('using'),
        field('left', choice($.parenthesized_expression, $._lhs_expression)),
        '=',
        field('right', $.expression),
      )),
  
      _augmented_assignment_lhs: $ => choice(
        $.member_expression,
        $.subscript_expression,
        alias($._reserved_identifier, $.identifier),
        $.identifier,
        $.parenthesized_expression,
        $.non_null_expression
      ),
  
      augmented_assignment_expression: $ => prec.right('assign', seq(
        field('left', $._augmented_assignment_lhs),
        field('operator', choice('+=', '-=', '*=', '/=', '%=', '^=', '&=', '|=', '>>=', '>>>=',
          '<<=', '**=', '&&=', '||=', '??=')),
        field('right', $.expression),
      )),
  
      _initializer: $ => seq(
        '=',
        field('value', $.expression),
      ),
  
      _destructuring_pattern: $ => choice(
        $.object_pattern,
        $.array_pattern,
      ),
  
      spread_element: $ => seq('...', $.expression),
  
      ternary_expression: $ => prec.right('ternary', seq(
        field('condition', $.expression),
        '?',
        field('consequence', $.expression),
        ':',
        field('alternative', $.expression),
      )),
  
      binary_expression: $ => choice(
        ...[
          ['&&', 'logical_and'],
          ['||', 'logical_or'],
          ['>>', 'binary_shift'],
          ['>>>', 'binary_shift'],
          ['<<', 'binary_shift'],
          ['&', 'bitwise_and'],
          ['^', 'bitwise_xor'],
          ['|', 'bitwise_or'],
          ['+', 'binary_plus'],
          ['-', 'binary_plus'],
          ['*', 'binary_times'],
          ['/', 'binary_times'],
          ['%', 'binary_times'],
          ['**', 'binary_exp', 'right'],
          ['<', 'binary_relation'],
          ['<=', 'binary_relation'],
          ['==', 'binary_equality'],
          ['===', 'binary_equality'],
          ['!=', 'binary_equality'],
          ['!==', 'binary_equality'],
          ['>=', 'binary_relation'],
          ['>', 'binary_relation'],
          ['??', 'ternary'],
          ['instanceof', 'binary_relation'],
          ['in', 'binary_relation'],
        ].map(([operator, precedence, associativity]) =>
          (associativity === 'right' ? prec.right : prec.left)(precedence, seq(
            field('left', operator === 'in' ? choice($.expression, $.private_property_identifier) : $.expression),
            field('operator', operator),
            field('right', $.expression),
          )),
        ),
      ),
  
      unary_expression: $ => prec.left('unary_void', seq(
        field('operator', choice('!', '~', '-', '+', 'typeof', 'void', 'delete')),
        field('argument', $.expression),
      )),
  
      update_expression: $ => prec.left(choice(
        seq(
          field('argument', $.expression),
          field('operator', choice('++', '--')),
        ),
        seq(
          field('operator', choice('++', '--')),
          field('argument', $.expression),
        ),
      )),
  
      sequence_expression: $ => prec.right(commaSep1($.expression)),
  
      string: $ => choice(
        seq(
          '"',
          repeat(choice(
            alias($.unescaped_double_string_fragment, $.string_fragment),
            $.escape_sequence,
          )),
          '"',
        ),
        seq(
          '\'',
          repeat(choice(
            alias($.unescaped_single_string_fragment, $.string_fragment),
            $.escape_sequence,
          )),
          '\'',
        ),
      ),
  
      unescaped_double_string_fragment: _ => token.immediate(prec(1, /[^"\\\r\n]+/)),
  
      unescaped_single_string_fragment: _ => token.immediate(prec(1, /[^'\\\r\n]+/)),
  
      escape_sequence: _ => token.immediate(seq(
        '\\',
        choice(
          /[^xu0-7]/,
          /[0-7]{1,3}/,
          /x[0-9a-fA-F]{2}/,
          /u[0-9a-fA-F]{4}/,
          /u\{[0-9a-fA-F]+\}/,
          /[\r?][\n\u2028\u2029]/,
        ),
      )),
  
      comment: $ => choice(
        token(choice(
          seq('//', /.*/),
          seq(
            '/*',
            /[^*]*\*+([^/*][^*]*\*+)*/,
            '/',
          ),
        )),
      ),
  
      _template_chars: $ => token(prec(1, /[^`$]|(\$[^{])/)),
  
      template_string: $ => seq(
        '`',
        repeat(choice(
          alias($._template_chars, $.string_fragment),
          $.escape_sequence,
          $.template_substitution,
        )),
        '`',
      ),
  
      template_substitution: $ => seq(
        '${',
        $._expressions,
        '}',
      ),
  
      regex: $ => seq(
        '/',
        field('pattern', $.regex_pattern),
        token.immediate(prec(1, '/')),
        optional(field('flags', $.regex_flags)),
      ),
  
      regex_pattern: _ => token.immediate(prec(-1,
        repeat1(choice(
          seq(
            '[',
            repeat(choice(
              seq('\\', /./), 
              /[^\]\n\\]/,
            )),
            ']',
          ), 
          seq('\\', /./), 
          /[^/\\\[\n]/, 
        )),
      )),
  
      regex_flags: _ => token.immediate(/[a-z]+/),
  
      _number: $ => prec.left(1, seq(
        field('operator', choice('-', '+')),
        field('argument', $.number),
      )),
  
      number: _ => {
        const hex_literal = seq(
          choice('0x', '0X'),
          /[\da-fA-F](_?[\da-fA-F])*/,
        );
  
        const decimal_digits = /\d(_?\d)*/;
        const signed_integer = seq(optional(choice('-', '+')), decimal_digits);
        const exponent_part = seq(choice('e', 'E'), signed_integer);
  
        const binary_literal = seq(choice('0b', '0B'), /[0-1](_?[0-1])*/);
  
        const octal_literal = seq(choice('0o', '0O'), /[0-7](_?[0-7])*/);
  
        const bigint_literal = seq(choice(hex_literal, binary_literal, octal_literal, decimal_digits), 'n');
  
        const decimal_integer_literal = choice(
          '0',
          seq(optional('0'), /[1-9]/, optional(seq(optional('_'), decimal_digits))),
        );
  
        const decimal_literal = choice(
          seq(decimal_integer_literal, '.', optional(decimal_digits), optional(exponent_part)),
          seq('.', decimal_digits, optional(exponent_part)),
          seq(decimal_integer_literal, exponent_part),
          seq(decimal_digits),
        );
  
        return token(choice(
          hex_literal,
          decimal_literal,
          binary_literal,
          octal_literal,
          bigint_literal,
        ));
      },
  
      _identifier: $ => choice(
        $.undefined,
        $.identifier,
      ),
  
      identifier: _ => {
        const alpha = /[^\x00-\x1F\s\p{Zs}0-9:;`"'@#.,|^&<=>+\-*/\\%?!~()\[\]{}\uFEFF\u2060\u200B]|\\u[0-9a-fA-F]{4}|\\u\{[0-9a-fA-F]+\}/;
        const alphanumeric = /[^\x00-\x1F\s\p{Zs}:;`"'@#.,|^&<=>+\-*/\\%?!~()\[\]{}\uFEFF\u2060\u200B]|\\u[0-9a-fA-F]{4}|\\u\{[0-9a-fA-F]+\}/;
        return token(seq(alpha, repeat(alphanumeric)));
      },
  
      private_property_identifier: _ => {
        const alpha = /[^\x00-\x1F\s\p{Zs}0-9:;`"'@#.,|^&<=>+\-*/\\%?!~()\[\]{}\uFEFF\u2060\u200B]|\\u[0-9a-fA-F]{4}|\\u\{[0-9a-fA-F]+\}/;
        const alphanumeric = /[^\x00-\x1F\s\p{Zs}:;`"'@#.,|^&<=>+\-*/\\%?!~()\[\]{}\uFEFF\u2060\u200B]|\\u[0-9a-fA-F]{4}|\\u\{[0-9a-fA-F]+\}/;
        return token(seq('#', alpha, repeat(alphanumeric)));
      },
  
      meta_property: _ => seq('new', '.', 'target'),
  
      this: _ => 'this',
      super: _ => 'super',
      true: _ => 'true',
      false: _ => 'false',
      null: _ => 'null',
      undefined: _ => 'undefined',
  
      arguments: $ => seq(
        '(',
        commaSep(optional(choice($.expression, $.spread_element))),
        ')',
      ),
  
      decorator: $ => seq(
        '@',
        choice(
          $.identifier,
          alias($.decorator_member_expression, $.member_expression),
          alias($.decorator_call_expression, $.call_expression),
        ),
      ),
  
      decorator_member_expression: $ => prec('member', seq(
        field('object', choice(
          $.identifier,
          alias($.decorator_member_expression, $.member_expression),
        )),
        '.',
        field('property', alias($.identifier, $.property_identifier)),
      )),
  
      decorator_call_expression: $ => prec('call', seq(
        field('function', choice(
          $.identifier,
          alias($.decorator_member_expression, $.member_expression),
        )),
        field('arguments', $.arguments),
      )),
  
      class_body: $ => seq(
        '{',
        repeat(choice(
          seq(
            repeat(field('decorator', $.decorator)),
            $.method_definition,
            optional($._semicolon),
          ),
          seq($.method_signature, choice(optional($._semicolon), ',')),
          $.class_static_block,
          seq(
            choice(
              $.abstract_method_signature,
              $.index_signature,
              $.method_signature,
              $.public_field_definition,
            ),
            choice($._semicolon, ','),
          ),
          ';',
        )),
        '}',
      ),
  
      field_definition: $ => seq(
        repeat(field('decorator', $.decorator)),
        optional('static'),
        field('property', $._property_name),
        optional($._initializer),
      ),
  
      formal_parameters: $ => seq(
        '(',
        optional(seq(
          commaSep1($._formal_parameter),
          optional(','),
        )),
        ')',
      ),
  
      class_static_block: $ => seq(
        'static',
        field('body', $.statement_block),
      ),
  
      pattern: $ => prec.dynamic(-1, choice(
        $._lhs_expression,
        $.rest_pattern,
      )),
  
      rest_pattern: $ => prec.right(seq(
        '...',
        $._lhs_expression,
      )),
  
      method_definition: $ => prec.left(seq(
        optional($.accessibility_modifier),
        optional('static'),
        optional($.override_modifier),
        optional('readonly'),
        optional('async'),
        optional(choice('get', 'set', '*')),
        field('name', $._property_name),
        optional('?'),
        $._call_signature,
        field('body', $.statement_block),
      )),
  
      pair: $ => seq(
        field('key', $._property_name),
        ':',
        field('value', $.expression),
      ),
  
      pair_pattern: $ => seq(
        field('key', $._property_name),
        ':',
        field('value', choice($.pattern, $.assignment_pattern)),
      ),
  
      _property_name: $ => choice(
        alias(choice(
          $.identifier,
          $._reserved_identifier,
        ), $.property_identifier),
        $.private_property_identifier,
        $.string,
        $.number,
        $.computed_property_name,
      ),
  
      computed_property_name: $ => seq(
        '[',
        $.expression,
        ']',
      ),
  
      _reserved_identifier: _ => choice(
        'get',
        'set',
        'async',
        'static',
        'export',
        'let',
        'declare',
        'namespace',
        'type',
        'public',
        'private',
        'protected',
        'override',
        'readonly',
        'module',
        'any',
        'number',
        'boolean',
        'string',
        'symbol',
        'export',
        'object',
        'new',
        'readonly',
      ),
  
      public_field_definition: $ => seq(
        repeat(field('decorator', $.decorator)),
        optional(choice(
          seq('declare', optional($.accessibility_modifier)),
          seq($.accessibility_modifier, optional('declare')),
        )),
        choice(
          seq(optional('static'), optional($.override_modifier), optional('readonly')),
          seq(optional('abstract'), optional('readonly')),
          seq(optional('readonly'), optional('abstract')),
        ),
        field('name', $._property_name),
        optional(choice('?', '!')),
        field('type', optional($.type_annotation)),
        optional($._initializer),
      ),
  
      _jsx_start_opening_element: $ => seq(
        '<',
        optional(
          seq(
            choice(
              field('name', choice(
                $._jsx_identifier,
                $.jsx_namespace_name,
              )),
              seq(
                field('name', choice(
                  $.identifier,
                  alias($.nested_identifier, $.member_expression),
                )),
                field('type_arguments', optional($.type_arguments)),
              ),
            ),
            repeat(field('attribute', $._jsx_attribute)),
          ),
        ),
      ),
  
      non_null_expression: $ => prec.left('unary', seq(
        $.expression, '!',
      )),
  
      method_signature: $ => seq(
        optional($.accessibility_modifier),
        optional('static'),
        optional($.override_modifier),
        optional('readonly'),
        optional('async'),
        optional(choice('get', 'set', '*')),
        field('name', $._property_name),
        optional('?'),
        $._call_signature,
      ),
  
      abstract_method_signature: $ => seq(
        optional($.accessibility_modifier),
        'abstract',
        optional($.override_modifier),
        optional(choice('get', 'set', '*')),
        field('name', $._property_name),
        optional('?'),
        $._call_signature,
      ),
  
      function_signature: $ => seq(
        optional('async'),
        'function',
        field('name', $.identifier),
        $._call_signature,
        $._semicolon,
      ),
  
      type_assertion: $ => prec.left('unary', seq(
        $.type_arguments,
        $.expression,
      )),
  
      as_expression: $ => prec.left('binary', seq(
        $.expression,
        'as',
        choice('const', $._type),
      )),
  
      satisfies_expression: $ => prec.left('binary', seq(
        $.expression,
        'satisfies',
        $._type,
      )),
  
      instantiation_expression: $ => prec('instantiation', seq(
        $.expression,
        field('type_arguments', $.type_arguments),
      )),
  
      extends_clause: $ => seq(
        'extends',
        commaSep1($._extends_clause_single),
      ),
  
      _extends_clause_single: $ => prec('extends', seq(
        field('value', $.expression),
        field('type_arguments', optional($.type_arguments)),
      )),
  
      implements_clause: $ => seq(
        'implements',
        commaSep1($._type),
      ),
  
      ambient_declaration: $ => seq(
        'declare',
        choice(
          $.declaration,
          seq('global', $.statement_block),
          seq('module', '.', alias($.identifier, $.property_identifier), ':', $._type, $._semicolon),
        ),
      ),
  
      module: $ => seq(
        'module',
        $._module,
      ),
  
      internal_module: $ => seq(
        'namespace',
        $._module,
      ),
  
      _module: $ => prec.right(seq(
        field('name', choice($.string, $.identifier, $.nested_identifier)),
        field('body', optional($.statement_block)),
      )),
  
      import_alias: $ => seq(
        'import',
        $.identifier,
        '=',
        choice($.identifier, $.nested_identifier),
        $._semicolon,
      ),
  
      nested_type_identifier: $ => prec('member', seq(
        field('module', choice($.identifier, $.nested_identifier)),
        '.',
        field('name', $._type_identifier),
      )),
  
      interface_declaration: $ => seq(
        'interface',
        field('name', $._type_identifier),
        field('type_parameters', optional($.type_parameters)),
        optional($.extends_type_clause),
        field('body', alias($.object_type, $.interface_body)),
      ),
  
      extends_type_clause: $ => seq(
        'extends',
        commaSep1(field('type', choice(
          $._type_identifier,
          $.nested_type_identifier,
          $.generic_type,
        ))),
      ),
  
      enum_declaration: $ => seq(
        optional('const'),
        'enum',
        field('name', $.identifier),
        field('body', $.enum_body),
      ),
  
      enum_body: $ => seq(
        '{',
        optional(seq(
          sepBy1(',', choice(
            field('name', $._property_name),
            $.enum_assignment,
          )),
          optional(','),
        )),
        '}',
      ),
  
      enum_assignment: $ => seq(
        field('name', $._property_name),
        $._initializer,
      ),
  
      type_alias_declaration: $ => seq(
        'type',
        field('name', $._type_identifier),
        field('type_parameters', optional($.type_parameters)),
        '=',
        field('value', $._type),
        $._semicolon,
      ),
  
      accessibility_modifier: _ => choice(
        'public',
        'private',
        'protected',
      ),
  
      override_modifier: _ => 'override',
  
      required_parameter: $ => seq(
        $._parameter_name,
        field('type', optional($.type_annotation)),
        optional($._initializer),
      ),
  
      optional_parameter: $ => seq(
        $._parameter_name,
        '?',
        field('type', optional($.type_annotation)),
        optional($._initializer),
      ),
  
      _parameter_name: $ => seq(
        repeat(field('decorator', $.decorator)),
        optional($.accessibility_modifier),
        optional($.override_modifier),
        optional('readonly'),
        field('pattern', choice($.pattern, $.this)),
      ),
  
      omitting_type_annotation: $ => seq('-?:', $._type),
      adding_type_annotation: $ => seq('+?:', $._type),
      opting_type_annotation: $ => seq('?:', $._type),
      type_annotation: $ => seq(
        ':',
        choice(
          $._type,
          alias($._type_query_member_expression_in_type_annotation, $.member_expression),
          alias($._type_query_call_expression_in_type_annotation, $.call_expression),
        ),
      ),
  
      _type_query_member_expression_in_type_annotation: $ => seq(
        field('object', choice(
          $.import,
          alias($._type_query_member_expression_in_type_annotation, $.member_expression),
          alias($._type_query_call_expression_in_type_annotation, $.call_expression),
        )),
        '.',
        field('property', choice(
          $.private_property_identifier,
          alias($.identifier, $.property_identifier),
        )),
      ),
  
      _type_query_call_expression_in_type_annotation: $ => seq(
        field('function', choice(
          $.import,
          alias($._type_query_member_expression_in_type_annotation, $.member_expression),
        )),
        field('arguments', $.arguments),
      ),
  
      asserts: $ => seq(
        'asserts',
        choice($.type_predicate, $.identifier, $.this),
      ),
  
      asserts_annotation: $ => seq(
        seq(':', $.asserts),
      ),
  
      _type: $ => choice(
        $._primary_type,
        $.function_type,
        $.readonly_type,
        $.constructor_type,
        $.infer_type,
      ),
  
      tuple_parameter: $ => seq(
        field('name', choice($.identifier, $.rest_pattern)),
        field('type', $.type_annotation),
      ),
  
      optional_tuple_parameter: $ => seq(
        field('name', $.identifier),
        '?',
        field('type', $.type_annotation),
      ),
  
      optional_type: $ => seq($._type, '?'),
      rest_type: ($) => seq('...', $._type),
  
      _tuple_type_member: $ => choice(
        alias($.tuple_parameter, $.required_parameter),
        alias($.optional_tuple_parameter, $.optional_parameter),
        $.optional_type,
        $.rest_type,
        $._type,
      ),
  
      constructor_type: $ => prec.left(seq(
        optional('abstract'),
        'new',
        field('type_parameters', optional($.type_parameters)),
        field('parameters', $.formal_parameters),
        '=>',
        field('type', $._type),
      )),
  
      _primary_type: $ => choice(
        $.parenthesized_type,
        $.predefined_type,
        $._type_identifier,
        $.nested_type_identifier,
        $.generic_type,
        $.object_type,
        $.array_type,
        $.tuple_type,
        $.flow_maybe_type,
        $.type_query,
        $.index_type_query,
        alias($.this, $.this_type),
        $.existential_type,
        $.literal_type,
        $.lookup_type,
        $.conditional_type,
        $.template_literal_type,
        $.intersection_type,
        $.union_type,
        'const',
      ),
  
      template_type: $ => seq('${', choice($._primary_type, $.infer_type), '}'),
  
      template_literal_type: $ => seq(
        '`',
        repeat(choice(
          alias($._template_chars, $.string_fragment),
          $.template_type,
        )),
        '`',
      ),
  
      infer_type: $ => prec.right(seq(
        'infer',
        $._type_identifier,
        optional(seq(
          'extends',
          $._type,
        )),
      )),
  
      conditional_type: $ => prec.right(seq(
        field('left', $._type),
        'extends',
        field('right', $._type),
        '?',
        field('consequence', $._type),
        ':',
        field('alternative', $._type),
      )),
  
      generic_type: $ => prec('call', seq(
        field('name', choice(
          $._type_identifier,
          $.nested_type_identifier,
        )),
        field('type_arguments', $.type_arguments),
      )),
  
      type_predicate: $ => seq(
        field('name', choice(
          $.identifier,
          $.this,
          alias($.predefined_type, $.identifier),
        )),
        'is',
        field('type', $._type),
      ),
  
      type_predicate_annotation: $ => seq(
        seq(':', $.type_predicate),
      ),
  
      _type_query_member_expression: $ => seq(
        field('object', choice(
          $.identifier,
          alias($._type_query_subscript_expression, $.subscript_expression),
          alias($._type_query_member_expression, $.member_expression),
          alias($._type_query_call_expression, $.call_expression),
        )),
        choice('.', '?.'),
        field('property', choice(
          $.private_property_identifier,
          alias($.identifier, $.property_identifier),
        )),
      ),
  
      _type_query_subscript_expression: $ => seq(
        field('object', choice(
          $.identifier,
          alias($._type_query_subscript_expression, $.subscript_expression),
          alias($._type_query_member_expression, $.member_expression),
          alias($._type_query_call_expression, $.call_expression),
        )),
        optional('?.'),
        '[', field('index', choice($.predefined_type, $.string, $.number)), ']',
      ),
  
      _type_query_call_expression: $ => seq(
        field('function', choice(
          $.import,
          $.identifier,
          alias($._type_query_member_expression, $.member_expression),
          alias($._type_query_subscript_expression, $.subscript_expression),
        )),
        field('arguments', $.arguments),
      ),
  
      _type_query_instantiation_expression: $ => seq(
        field('function', choice(
          $.import,
          $.identifier,
          alias($._type_query_member_expression, $.member_expression),
          alias($._type_query_subscript_expression, $.subscript_expression),
        )),
        field('type_arguments', $.type_arguments),
      ),
  
      type_query: $ => prec.right(seq(
        'typeof',
        choice(
          alias($._type_query_subscript_expression, $.subscript_expression),
          alias($._type_query_member_expression, $.member_expression),
          alias($._type_query_call_expression, $.call_expression),
          alias($._type_query_instantiation_expression, $.instantiation_expression),
          $.identifier,
        ),
      )),
  
      index_type_query: $ => seq(
        'keyof',
        $._primary_type,
      ),
  
      lookup_type: $ => seq(
        $._primary_type,
        '[',
        $._type,
        ']',
      ),
  
      mapped_type_clause: $ => seq(
        field('name', $._type_identifier),
        'in',
        field('type', $._type),
        optional(seq('as', field('alias', $._type))),
      ),
  
      literal_type: $ => choice(
        alias($._number, $.unary_expression),
        $.number,
        $.string,
        $.true,
        $.false,
        $.null,
        $.undefined,
      ),
  
      existential_type: _ => '*',
  
      flow_maybe_type: $ => prec.right(seq('?', $._primary_type)),
  
      parenthesized_type: $ => seq('(', $._type, ')'),
  
      predefined_type: _ => choice(
        'any',
        'number',
        'boolean',
        'string',
        'symbol',
        alias(seq('unique', 'symbol'), 'unique symbol'),
        'void',
        'unknown',
        'string',
        'never',
        'object',
      ),
  
      type_arguments: $ => seq(
        '<',
        commaSep1(choice(
          $._type,
          alias($._type_query_member_expression_in_type_annotation, $.member_expression),
          alias($._type_query_call_expression_in_type_annotation, $.call_expression),
        )),
        optional(','),
        '>',
      ),
  
      object_type: $ => seq(
        choice('{', '{|'),
        optional(seq(
          optional(choice(',', ';')),
          sepBy1(
            choice(',', $._semicolon),
            choice(
              $.export_statement,
              $.property_signature,
              $.call_signature,
              $.construct_signature,
              $.index_signature,
              $.method_signature,
            ),
          ),
          optional(choice(',', $._semicolon)),
        )),
        choice('}', '|}'),
      ),
  
      property_signature: $ => seq(
        optional($.accessibility_modifier),
        optional('static'),
        optional($.override_modifier),
        optional('readonly'),
        field('name', $._property_name),
        optional('?'),
        field('type', optional($.type_annotation)),
      ),
  
      type_parameters: $ => seq(
        '<', commaSep1($.type_parameter), optional(','), '>',
      ),
  
      type_parameter: $ => seq(
        optional('const'),
        field('name', $._type_identifier),
        field('constraint', optional($.constraint)),
        field('value', optional($.default_type)),
      ),
  
      default_type: $ => seq(
        '=',
        $._type,
      ),
  
      constraint: $ => seq(
        choice('extends', ':'),
        $._type,
      ),
  
      construct_signature: $ => seq(
        optional('abstract'),
        'new',
        field('type_parameters', optional($.type_parameters)),
        field('parameters', $.formal_parameters),
        field('type', optional($.type_annotation)),
      ),
  
      index_signature: $ => seq(
        optional(
          seq(
            field('sign', optional(choice('-', '+'))),
            'readonly',
          ),
        ),
        '[',
        choice(
          seq(
            field('name', choice(
              $.identifier,
              alias($._reserved_identifier, $.identifier),
            )),
            ':',
            field('index_type', $._type),
          ),
          $.mapped_type_clause,
        ),
        ']',
        field('type', choice(
          $.type_annotation,
          $.omitting_type_annotation,
          $.adding_type_annotation,
          $.opting_type_annotation,
        )),
      ),
  
      array_type: $ => seq($._primary_type, '[', ']'),
      tuple_type: $ => seq(
        '[', commaSep($._tuple_type_member), optional(','), ']',
      ),
      readonly_type: $ => seq('readonly', $._type),
  
      union_type: $ => prec.left(seq(optional($._type), '|', $._type)),
      intersection_type: $ => prec.left(seq(optional($._type), '&', $._type)),
  
      function_type: $ => prec.left(seq(
        field('type_parameters', optional($.type_parameters)),
        field('parameters', $.formal_parameters),
        '=>',
        field('return_type', choice($._type, $.asserts, $.type_predicate)),
      )),
  
      _type_identifier: $ => alias($.identifier, $.type_identifier),
      
      _semicolon: $ => ';',
    },
  });
  
  function commaSep1(rule) {
    return seq(rule, repeat(seq(',', rule)));
  }
  
  function commaSep(rule) {
    return optional(commaSep1(rule));
  }
  
  function sepBy1(sep, rule) {
    return seq(rule, repeat(seq(sep, rule)));
  }
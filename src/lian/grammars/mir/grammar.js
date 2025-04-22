const PREC = {
    COMMENT: 0, 
    ASSIGN: 1,         // Assignment operators
    RETURN: 1,         // return statement
    STATEMENT: 2,      // Statements
    OR: 2,             // ||
    AND: 3,            // &&
    BIT_OR: 4,         // |
    BIT_XOR: 5,        // ^
    BIT_AND: 6,        // &
    EQUALITY: 7,       // ==  !=
    REL: 8,            // <  <=  >  >=
    SHIFT: 9,          // <<  >>  >>>
    ADD: 10,           // +  -
    MULT: 11,          // *  /  %
    UNARY: 12,         // Unary operators like -a, !a
    COPY: 12,          // copy_expression
    MOVE: 12,          // move_expression
    CALL: 13,          // Function calls
    FIELD : 13,
    PARENS: 14,        // (Expression)
    ARRAY: 14,         // [Expression]
    PATH: 15,          // a::b
    PATH_SEGMENT: 16,  // a::b::c
  };
  
  module.exports = grammar({
    name: 'mir',
  
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
      [$._base_lvalue],
      [$.type, $.path_type],
      [$.dereference_expression],
      [$.expression,$.repeat_rvalue],
      [$.expression, $.list_rvalue],
      [$.expression, $.parenthesized_lvalue],
      [$.tuple_expression, $.constant],
      [$.generic_args, $.path_segment],
      [$.expression, $.field_access_lvalue],
      [$.const_expression, $.path_type],
      [$.constant_rvalue, $.cast_expression],
      [$._base_lvalue, $.dereference_expression],
      [$.constant_rvalue,$.constant],
      [$.path_segment, $.function_name],
      [$._base_lvalue, $.dereference_lvalue],
      [$.impl_at, $.special_function_name],
      [$.constant_with_type, $.cast_expression],
      [$.path_segment, $.function_name, $._base_lvalue],
      [$.path_segment, $.function_name, $.field_access_lvalue],
      [$.path_segment, $.function_name, $.cast_annotation],
      [$.move_expression, $.tuple_expression, $.parenthesized_expression],
      [$.expression, $.parenthesized_lvalue, $.copy_expression],
      [$.path_segment, $.function_name, $._base_lvalue, $.cast_annotation],
      [$.path_segment, $.function_name, $._base_lvalue, $.type_cast_lvalue],
      [$.copy_expression, $.tuple_expression, $.parenthesized_expression],
    ],
      
    word: $ => $.identifier,
  
    rules: {
      program: $ => repeat($._toplevel_statement),
      
      _toplevel_statement: $ => choice(
        $.declaration,
        $.statement,
      ),
  
      // Types
      type: $ => choice(
        $.primitive_type,          
        $.pointer_type,            
        $.array_type,              
        $.tuple_type,              
        $.reference_type,  
        $.qualified_path,  // <Type as Trait>::method
        $.path_type,       // Prefix Path
        $.impl_type,       // impl Type
        $.impl_at,  
        $.never_reaches,   // '!'           
      ),
      
      primitive_type: $ => choice(
        'i32', 'u32', 'i64', 'u64', 'f32', 'f64', 'bool', 'char', 'str', 'usize',"()"
      ),
      
      pointer_type: $ => seq(
        field('pointer', choice('*const', '*mut')),
        field('referenced_type', $.type)
      ),
      
      array_type: $ => seq(
        '[',
        field('array_type', $.type),
        optional(seq(';', field('length', $.int))),  
        ']'
      ),
      
      tuple_type: $ => seq(
        '(',
        commaSep1(field('element_type', $.type)),
        ')'
      ),
    
      reference_type: $ => prec(PREC.UNARY, seq(
        '&',
        optional(seq("'", field('lifetime', $.region))),  
        optional(field('mutable', 'mut')),
        field('referenced_type', $.type)
      )),
  
      qualified_path: $ => prec.left(PREC.PATH_SEGMENT, seq(
        '<',
        choice(
          $.type,
          $.impl_at        
        ),
        optional(seq(
          'as',
          $.path_type,
        )),
        '>',
        '::',
        sep1($.path_segment, '::'),
        optional($.array_index),
        optional(':'),
        optional($.type),         // such as &i32
      )),
      
      impl_type: $ => seq(
        'impl',
        field('implemented_type', $.type)
      ),    
  
      impl_at: $ => seq(
        'impl',
        'at',
        field('file_location', $.file_location)   // Process file location, such as drop.rs:5:1: 5:23
      ),
  
      path_segment: $ => prec.left(seq(
        field('identifier', $.identifier),
        optional(field('generic_arguments', $.generic_args))
      )),
      
      generic_args: $ => choice(
        seq('<', commaSep1(choice($.type, $.region, $.int, $.identifier)), '>'),
        seq('::<', commaSep1(choice($.type, $.region, $.int, $.identifier)), '>')
      ),
  
      path_type: $ => choice(
        prec.left(PREC.PATH, seq(
          optional('::'),
          field('segments', sep1($.path_segment, '::')),
          repeat($.array_index), 
        )),
        $.qualified_path,
      ),
  
      array_index: $ => seq(
        '[',
        field('index', $.int),
        ']'
      ),
  
      never_reaches: $ => field('never_reaches', '!'),
  
      // Declarations
      parameters: $ => commaSep1($.parameter),
  
      parameter: $ => seq(
        field('name', $.identifier),
        ':',
        field('type', $.type)
      ),
  
      declaration: $ => choice(
        $.variable_declaration,
        $.const_declaration,
        $.function_declaration,
      ),
  
      variable_declaration: $ => seq(
        'let',
        optional(field('mutable', 'mut')),
        field('name', $.identifier),
        ':',
        choice(
          field('type', $.type),          // When a type is present, no parentheses
          seq('(', ')')                    // When no type, match empty parentheses
        ),
        ';'
      ),
  
      const_declaration: $ => prec.left(seq(
        'const',
        field('name', $.path_type),       // test_array_slice::promoted[0]
        ':',
        field('type', $.type),            // &[&str; 2]
        '=',
        optional(field('value', $.const_expression)), 
        optional(';')
      )),
  
      function_header: $ => prec.left(seq(
        'fn',
        field('name', $.function_name),
        '(',
        optional(field('parameters', $.parameters)),
        ')',
        '->',
        field('return_type', choice($.type, seq('(', ')') )),  
      )),
  
      function_body: $ => seq(
        '{',
        repeat($.declaration),  
        repeat($.statement),    
        '}',
      ),
  
      function_declaration: $ => prec.left(seq(
        $.function_header,
        optional($.function_body),
      )),
   
  
      function_name: $ => choice(
        $.identifier,
        $.path_type,
        $.special_function_name,
      ),
  
      special_function_name: $ => seq(
        '<',
        'impl',
        'at',
        field('file_location', $.file_location),
        '>',
        '::',
        field('identifier', $.identifier),
      ),
      
      path: $ => prec.left(seq(
        field('root', optional('::')),
        field('segments', sep1($.path_segment, '::'))
      )),
      
      file_location: $ => token(/[^>]+/),
  
      // Statements
      statement: $ => prec(PREC.STATEMENT, choice(
        $.variable_declaration,
        $.assignment_statement,
        $.drop_statement,
        $.return_statement,
        $.basic_block,
        $.scope,
        $.debug_statement,
        $.assert_statement,
        $.unreach_statement,
        $.resume_statement,
      )),
  
      assignment_statement: $ => prec.left(PREC.ASSIGN, seq(
        field('left',$.lvalue),
        '=',
        field('right', $.expression), 
        ';',
      )),
  
      drop_statement: $ => seq(
        'drop',
        '(',
        field('kind', $.drop_kind),
        ',',
        field('value', $.lvalue),
        ')',
        ';'
      ),
  
      drop_kind: $ => choice(
        'shallow', 
        'deep'
      ),
  
      return_statement: $ => prec.left(PREC.RETURN, seq(
        'return',
        optional(field('value', $.expression)),
        ';',
      )),
  
      basic_block: $ => seq(
        field('label', $.basic_block_label),
        ':',
        '{',
        repeat($.statement),
        optional(field('terminator', $.terminator)),
        '}',
      ),
  
      terminator: $ => choice(
        $.goto_terminator,
        $.panic_terminator,
        $.if_terminator,
        $.switchInt_terminator,
        $.call_terminator,
        $.drop_terminator,
        $.diverge_terminator,
        $.return_terminator,
      ),
  
      // Individual terminator rules
      goto_terminator: $ => seq(
        'goto', 
        optional('('),
        '->',
        field('target', $.basic_block_label), 
        optional(')'), 
        ';'
      ),
  
      panic_terminator: $ => seq(
        'panic', 
        '(', 
        field('target', $.basic_block_label), 
        ')', 
        ';'
      ),
  
      if_terminator: $ => seq(
        'if', 
        '(', 
        field('condition', $.lvalue), 
        ',', 
        field('true_target', $.basic_block_label),  
        ',', 
        field('false_target', $.basic_block_label),  
        ')', 
        ';'
      ),
  
      switchInt_terminator: $ => seq(
        'switchInt',
        '(',
        field('expression', $.expression),  
        ')',
        optional(seq(
          '->',
          '[',
          field('jump_targets', $.jump_targets),  
          ']'
        )),
        ';'
      ),
  
      call_terminator: $ => seq(
        'call',
        '(',
        field('result', $.lvalue),
        '=',
        field('function', $.function_name),
        '(',
        optional(commaSep1($.expression)),
        ')',
        ',',
        field('true_target', $.basic_block_label), 
        ',',
        field('false_target', $.basic_block_label), 
        ')',
        ';'
      ),
  
      drop_terminator: $ => seq(
        'drop',
        '(',
        field('value', $.lvalue),
        ')',
        optional(seq(
          '->',
          '[',
          field('jump_targets', $.jump_targets),
          ']'
        )),
        ';'
      ),
  
      diverge_terminator: $ => seq(
        'diverge',
        ';'
      ),
  
      return_terminator: $ => seq(
        'return',
        ';'
      ),
  
      basic_block_label: $ => seq(
        /bb[0-9]+/,
        optional(seq(
          '(',
          field('name', $.identifier),
          ')'
        ))
      ),
  
      scope: $ => seq(
        'scope',
        field('scope_label', $.int),   
        '{',
        repeat($.statement), 
        '}'
      ),
  
      debug_statement: $ => seq(
        'debug',
        field('variable', $.identifier),     
        '=>',
        field('value', $.debug_value),
        ';'
      ),
  
      debug_value: $ => choice(
        $.const_expression, // const 10_i32 
        $.identifier,      //  _2, _9 
      ),
  
      constant_with_type: $ => seq(
        field('constant', $.constant),    
        optional(field('type_suffix', $.type_suffix)), // Type with suffix 
      ),
  
      type_suffix: $ => token(seq(
        optional('_'),            
        /[a-zA-Z][a-zA-Z0-9_]*/  // Type suffix，such as i32, u32, f64
      )),
  
      assert_statement: $ => prec.left(seq(
        'assert',
        '(',
        optional('!'),
        field('condition', $.expression),
        optional(seq(
          ',',
          field('message', $.static_string),
          repeat(seq(',', $.expression))
        )),
        ')',
        optional(seq(
          '->',
          optional('['),
          field('jump_targets', $.jump_targets),
          optional(']')
        )),
        ';'
      )),
  
      jump_targets: $ => commaSep1($.jump_target),
  
      jump_target: $ => seq(
        field('key', $.jump_target_key),
        optional(':'),
        field('value', choice(
          $.return,    
          $.continue,
          $.terminate,
          $.unreachable,
          $.basic_block_label,
          $.unwind_expression 
        ))
      ),
  
      return: $ => 'return',
  
      continue: $ => 'continue',
  
      unreachable: $ => 'unreachable',
  
      terminate: $ => choice(
        'terminate', 
        seq('terminate', '(', 'cleanup', ')'),   
      ),
  
      jump_target_key: $ => choice(
        $.int,
        'otherwise',
        'success',
        'return',
        'unwind'
      ),
  
      unreach_statement: $ => seq(
        'unreachable',
        ';'
      ),
  
      resume_statement: $ => seq(
        'resume',
        ';'
      ),
  
      // Expressions
      expression: $ => choice(
        $.function_call_expression,
        $.unary_expression,
        $.copy_expression,    
        $.move_expression,      
        //$.field_access_expression, 
        $.lvalue,
        $.rvalue,
        $.const_expression,   
        $.tuple_expression,  
        $.array_expression,  
        $.as_expression,
        $.struct_initialization_expression,
        $.complex_value,
        $.parenthesized_expression,
        $.dereference_expression,
        $.cast_annotation,
      ),
  
      unary_expression: $ => prec.left(PREC.UNARY, choice(
        seq(field('operator', '!'), field('argument', $.expression)),
        seq(field('operator', '-'), field('argument', $.expression)),
        field('address_of', $.address_of_expression),
        field('dereference', $.dereference_expression),
      )),
  
      // L-values
      lvalue: $ => choice(
        $._base_lvalue,
        $.annotated_lvalue,   
        $.field_access_lvalue,
        $.array_access_lvalue,
        $.dereference_lvalue,  
        $.type_cast_lvalue,
        $.parenthesized_lvalue,  
        
      ),    
    
      _base_lvalue: $ => choice(
        $.identifier, 
        seq('*', $.identifier) 
      ),
  
      annotated_lvalue: $ => prec.left(seq(
        field('lvalue', $.lvalue),
        ':',
        field('type', $.type)
      )),
  
      // Split _compound_lvalue into individual rules
      field_access_lvalue: $ => prec.left(seq(
        field('object', $.lvalue),  
        '.',
        field('field', choice($.identifier, $.int))  
      )),    
      
      array_access_lvalue: $ => seq(
        field('object', $._base_lvalue),
        '[',
        field('index', $.expression),
        ']'
      ),
      
      dereference_lvalue: $ => prec.left(PREC.UNARY , seq(
        '*',
        field('operand', $.lvalue)
      )),
  
      parenthesized_lvalue: $ => seq(
        '(',
        $.lvalue,
        ')'
      ),    
      
      type_cast_lvalue: $ => seq(
        '(',
        field('identifier', $.identifier),
        'as',
        field('type', $.type),
        ')'
      ),
  
      // Split _rvalue into individual rules
      rvalue: $ => choice(
        $.use_rvalue,
        $.repeat_rvalue,
        $.list_rvalue,
        $.length_rvalue,
        $.indexed_rvalue,
        $.box_rvalue,
        $.constant_rvalue,
        //$.block_rvalue,
      ),
  
      use_rvalue: $ => seq(
        'use',
        '(',
        field('lvalue', $.lvalue),
        ')'
      ),
  
      repeat_rvalue: $ => seq(
        '[',
        field('lvalue1', $.lvalue),
        ';',
        field('lvalue2', $.lvalue),
        ']'
      ),
  
      list_rvalue: $ => seq(
        '[',
        commaSep1(field('elements', $.lvalue)),
        ']'
      ),
  
      length_rvalue: $ => seq(
        'len',
        '(',
        field('lvalue', $.lvalue),
        ')'
      ),
  
      indexed_rvalue: $ => seq(
        field('identifier', $.identifier),
        '[',
        field('index', $.expression),
        ']'
      ),
  
      box_rvalue: $ => 'box',
  
      constant_rvalue: $ => $.constant,
  
      //block_rvalue: $ => $.block,
  
      // Function Call Expression
      function_call_expression: $ => prec(PREC.CALL, seq(
        field('function', $.function_name),  
        optional(seq(
          '(',
          field('arguments', commaSep($.expression)),  // arguments
          ')',
        )),
        optional(seq(
          '->',
          choice(field('basic_block_label', $.basic_block_label), field('unwind_expression', $.unwind_expression)),   
        )),
        optional(seq(
          '->',
          '[',
          field('jump_targets', $.jump_targets),
          ']'
        ))
      )),
      
      unwind_expression: $ => seq(
        'unwind',
        field('value', choice($.identifier, 'continue', 'terminate', seq('terminate', '(', 'cleanup', ')')))
      ),
  
      const_expression: $ => seq(
        'const',
        choice(
          $.constant_with_type,
          $.path_type,
          $.qualified_path,
          //$.block,
        )   
      ),
  
      copy_expression: $ => prec.left(PREC.COPY, seq(
        'copy',
        optional('('),
        field('value', $.expression),  
        optional(')'),
      )),    
      
      move_expression: $ => prec.left(PREC.MOVE, seq(
        'move',
        optional('('),
        field('value', $.expression),
        optional(')'),
      )),    
      
      // field_access_expression: $ => prec.left(PREC.FIELD, seq(
      //   field('value', $.expression),
      //   '.',
      //   field('field', choice($.identifier, $.int)),  
      //   optional(seq(':', field('type', $.type))),    
      // )),    
  
      dereference_expression: $ => prec.left(PREC.UNARY , seq(
        '*',
        field('operand', $.expression)
      )),
      
      address_of_expression: $ => prec.left(PREC.UNARY, seq(
        '&',
        optional(seq("'", field('lifetime', $.region))),  
        optional(field('mutable', 'mut')),               
        field('operand', $.expression)
      )),
  
      tuple_expression: $ => seq(
        '(',
        commaSep($.expression),  
        ')'
      ),
  
      array_expression: $ => prec.left(PREC.ARRAY, choice(
        // [expr; expr] 
        seq(
          optional(field('label', $.identifier)),
          '[',
          field('array_elements', $.expression), 
          ';',
          field('length', $.expression), 
          ']'
        ),
  
        // [expr, expr] 
        seq(
          optional(field('label', $.identifier)),
          '[',
          choice(field('single', $.identifier), commaSep1(field('elements', $.expression))), 
          ']'
        )
      )),
          
      as_expression: $ => prec(PREC.CALL, seq(
        field('expression', $.expression),        
        'as',                
        field('type', $.type),
        optional(field('cast_annotation', $.cast_annotation))               
      )),
  
      cast_annotation: $ => seq(
        '(',
        field('annotation', $.identifier),
        optional(seq(
          '(',
          field('inner_annotation', $.identifier),
          ')'
        )),
        ')'
      ),
      
      struct_initialization_expression: $ => seq(
        field('struct_type', $.path_type),
        '{',
        sep1(field('fields', $.struct_field_initialization), ','),  // field initialization
        optional(','),  
        '}'
      ),
      
      struct_field_initialization: $ => seq(
        field('field_name', $.identifier),  
        ':',
        field('value', $.expression)   
      ),    
  
      complex_value: $ => prec.left(-1, seq(
        optional('const'),
        field('path', $.path_type),             
        '[',
        field('index', $.int),                   
        ']',
        optional(':'),
        optional(field('type', $.type))         
      )),
  
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
        $.trait_projection,          //  (<P0 as TRAIT<P1...Pn>>)
        $.constant_aggregate,        //  (Struct { (f: CONSTANT)... })
        $.cast_expression,           //  (CAST)
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
  
      // (CAST(CONSTANT, TY)
      cast_expression: $ => seq(
        field('constant', $.constant),
        'as',
        field('type', $.type)
      ),
  
      // (Struct { (f: CONSTANT)... })
      constant_aggregate: $ => seq(
        field('struct_name', $.identifier), 
        '{',
        commaSep(field('field_initialization', $.struct_field_initialization)), 
        optional(','),  
        '}'
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
  

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
  name: "abc",

  extras: $ => [
    $.comment,
    /\s/,  // Whitespace
   
  ],

  word: $ => $.identifier,

  rules: {
    // TODO: add the actual grammar rules
    

    // @ts-ignore
    program: $ => repeat($._toplevel_statement),
    
    _toplevel_statement: $ => choice(
      $.declaration,
      $.statement,
    ),

    type: $ => choice(
      'i32', 'u32', 'i64', 'u64', 'f32', 'f64', 'bool', 'char', 'string', 'usize',"()", "any","null_value",
    ),

    declaration: $ => choice(
      $.function_declaration,
    ),

    function_header: $ => prec.left(seq(
      'L_ESSlotNumberAnnotation:', 'u32', 'slotNumberIdx', '{', $.hexi,'}',
      '.function',
      'any',
      choice(
        $.function_name_type1,
        field('name', $.dot_separated_identifiers),
      ),
      '(',
      optional(field('parameters', $.parameters)),
      ')',
      '<',
      field('return_type', $.identifier),
      '>'
      //field('return_type', choice($.type, seq('(', ')') )),  
    )),

    parameters: $ => commaSep1($.parameter),

    parameter: $ => seq(
      field('type', $.type),
      
      field('name', $.identifier)
    ),

    function_body: $ => seq(
      '{',
      repeat(
        choice(
          $.declaration,
          $.statement,
        )
      ),  
      
      '}',
    ),

    function_declaration: $ => prec.left(seq(
      $.function_header,
      optional($.function_body),
    )),

    function_name_type1: $ => prec(1, seq(
      '&',
      field('file_path', $.file_path),
      '&',
      '.',
      field('name', choice($.identifier, $.temp_name)),

    )),

    file_path: $ => $.dot_separated_identifiers,

    dot_separated_identifiers: $ => seq(
      $.identifier,                   // 起始标识符
      repeat(seq('.', $.identifier))  // 后续以 . 分隔的标识符
    ),
    
    temp_name: $ => seq(
      '#',
      $.deci,
      '#',
      choice(
        $.identifier,
      )
    ),

    statement: $ => prec(PREC.STATEMENT, choice(
      $.declaration,
      $.sta_statement,
      $.lda_statement,
      $.ldastr_statement,
      $.ldtrue_statement,
      $.ldlexvar_statement,
      $.ldundefiened_statement,
      $.ldai_statement,
      $.ldobjbyname_statement,
      $.ldexternalmodulevar_statement,
      $.ldhole_statement,
      $.ldnull_statement,
      $.call_statement,
      $.callthis0_statement,
      $.callthis1_statement,
      $.callthis2_statement,
      $.callthis3_statement,
      $.callarg1_statement,
      $.callargs2_statement,
      $.callargs3_statement,
      $.definefunc_statement,
      $.definemethod_statement,
      $.definefieldbyname_statement,
      $.defineclass_statement,
      $.mov_statement,
      $.tryldglobalbyname_statement,
      $.stlexvar_statement,
      $.stmodulevar_statement,
      $.stownbyindex_statement,
      $.stownbyname_statement,
      $.stobjbyname_statement,
      $.cmp_statement,
      $.if_statement,
      $.returnundefined_statement,
      $.return_statement,
      $.new_array_statement,
      $.newobjrange_statement,
      $.newenv_statement,
      $.add_statement,
      $.tonumeric_statement,
      $.ifhole_statement,
      $.condition_statement,
      $.strictnoteq_statement,
      $.stricteq_statement,
      $.inc_statement,
      $.while_statement,
      $.copyrestargs_statement,
      $.supercallspread_statement,
      $.throwcallwrong_statement,
      $.asyncfunctionenter_statement,
      $.neg_statement,
      $.asyncfunctionawaituncaught_statement,
      $.asyncfunctionreject_statement,
      $.asyncfunctionresolve_statement,
      $.suspendgenerator_statement,
      $.getresumemode_statement,
      $.createemptyarray_statement,
      $.createobjectwithbuffer_statement,
      $.createemptyobject_statement,
      $.isin_statement,
    )),

    sta_statement: $ => seq(
      'sta',
      field('register', $.identifier),
    ),

    lda_statement: $ => seq(
      'lda',
      field('register', $.identifier),
    ),


    ldastr_statement: $ => seq(
      'lda.str',
      field(
        'string', 
          $.string,
      ),
    ),

    ldtrue_statement: $ => 'ldtrue',

    ldlexvar_statement: $ => seq(
      'ldlexvar',
      field('lexi_env', $.hexi),
      ',',
      field('slot', $.hexi),
    ),

    ldundefiened_statement: $ => 'ldundefined',

    ldai_statement: $ => seq(
      'ldai',
      field('imm', $.hexi),
    ),

    ldobjbyname_statement: $ => seq(
      'ldobjbyname',
      field('reserve', $.hexi),
      ',',
      '"',
      field('object',$.identifier,),
      '"'
    ),

    ldexternalmodulevar_statement: $ => seq(
      'ldexternalmodulevar',
      field('slot', $.hexi),
    ),

    ldhole_statement: $ => "ldhole",

    ldnull_statement: $ => "ldnull",

    call_statement: $ => seq(
      'callarg0',
      field('reserve', $.hexi),
    ),

    callthis0_statement: $ => seq(
      'callthis0',
      field('reserve', $.hexi),
      ',',
      field('this', $.identifier),
    ),
    callthis1_statement: $ => seq(
      'callthis1',
      field('reserve', $.hexi),
      ',',
      field('this', $.identifier),
      ',',
      field('arg1', $.identifier),
    ),

    callthis2_statement: $ => seq(
      'callthis2',
      field('reserve', $.hexi),
      ',',
      field('this', $.identifier),
      ',',
      field('arg1', $.identifier),
      ',',
      field('arg2', $.identifier),
    ),

    callthis3_statement: $ => seq(
      'callthis2',
      field('reserve', $.hexi),
      ',',
      field('this', $.identifier),
      ',',
      field('arg1', $.identifier),
      ',',
      field('arg2', $.identifier),
      ',',
      field('arg3', $.identifier),
    ),

    callarg1_statement: $ => seq(
      'callarg1',
      field('reserve', $.hexi),
      ',',
      field('arg1', $.identifier),
    ),

    callargs2_statement: $ => seq(
      'callargs2',
      field('reserve', $.hexi),
      ',',
      field('arg1', $.identifier),
      ',',
      field('arg2', $.identifier),
    ),

    callargs3_statement: $ => seq(
      'callargs3',
      field('reserve', $.hexi),
      ',',
      field('arg1', $.identifier),
      ',',
      field('arg2', $.identifier),
      ',',
      field('arg3', $.identifier),
    ),

    mov_statement: $ => seq(
      'mov',
      field('v1', $.identifier),
      ',',
      field('v2', $.identifier),
    ),

    stlexvar_statement: $ => seq(
      'stlexvar',
      field('lexi_env', $.hexi),
      ',',
      field('slot', $.hexi),
    ),

    stmodulevar_statement: $ => seq(
      'stmodulevar',
      field('slot', $.hexi),
    ),

    stownbyindex_statement: $ => seq(
      'stownbyindex',
      field('reserve', $.hexi),
      ',',
      field('object', $.identifier),
      ',',
      field('index', $.hexi),
    ),

    stownbyname_statement: $ => seq(
      'stownbyname',
      field('reserve', $.hexi),
      ',',
      field('object', $.string),
      ',',
      field('name', $.identifier),
    ),

    stobjbyname_statement: $ => seq(
      'stobjbyname',
      field('reserve', $.hexi),
      ',',
      '"',
      field('field',$.identifier,),
      '"',
      ',',
      field('object', $.identifier),
    ),

    new_array_statement: $ => seq(
      'createarraywithbuffer',
      $.hexi,
      ',',
      $.literal,
    ),

    newobjrange_statement: $ => seq(
      'newobjrange',
      field('reserve', $.hexi),',',
      field('param_num', $.hexi),',',
      field('object', $.identifier),
    ),

    newenv_statement: $ => seq(
      'newlexenvwithname',
      field('slot_number', $.hexi),
      ',',
      $.literal,
    ),


    definefunc_statement: $ => seq(
      'definefunc',
      field('reserve', $.hexi),',',
      $.method_decl,
      field('args_number', $.hexi),
      
    ),

    definemethod_statement: $ => seq(
      'definemethod ',
      field('reserve', $.hexi),',',
      $.method_decl,
      field('args_number', $.hexi),
    ),

    definefieldbyname_statement: $ => seq(
      'definefieldbyname',
      field('reserve', $.hexi),',',
      field('field', $.string),',',
      field('object', $.identifier),
    ),

    defineclass_statement: $ => seq(
      'defineclasswithbuffer',
      field('reserve', $.hexi),',',
      $.method_decl,
      $.literal,
      ',',
      field('formal_paranum', $.hexi),
      ',',
      field('super', $.identifier),
    ),

    method_decl: $ => seq(
      $.dot_separated_identifiers,
      ':(',
      commaSep1($.type),
      '),',
    ),

    ifhole_statement: $ => seq(
      'throw.undefinedifholewithname',
      '"',
      $.string,
      '"',
    ),

    cmp_statement: $ => seq(
      choice(
        'greater',
        'less',
      ),
      field('reserve', $.hexi),
      ',',
      field('register', $.identifier),
    ),

    isfalse_statement: $ => 'isfalse',  

    if_statement: $ => seq(
      field(
        'condition',
        $.condition_statement,
      ),
      field('consequence', $.consequence_statement),
      field('alternative', $.alternative_statement),

    ),

    condition_statement: $ => choice($.cmp_statement, $.isfalse_statement),
    while_condition_statement: $ => choice($.cmp_statement, $.isfalse_statement),
    while_statement: $ => seq(
      $.condition_statement,
      choice(
        $.jeqz_statement,
        $.jnez_statement,
      ),
      repeat($.statement),
      $.jmploop_statement,
      $.label_statement,
    ),

    consequence_statement: $ => seq(
      choice(
        $.jeqz_statement,
        $.jnez_statement,
      ),
      repeat($.statement),
      $.jmp_statement,
    ),


    alternative_statement: $ => seq(
      $.label_statement,
      repeat($.statement),
      // optional($.label_statement),
      $.label_statement,
    ),

    jeqz_statement: $ => seq(
      'jeqz',
      field('target', $.identifier),
    ),

    jnez_statement: $ => seq(
      'jnez',
      field('target', $.identifier),
    ),

    jmp_statement: $ => seq(
      'jmp',
      field('target', $.identifier),
    ),

    jmploop_statement: $ => seq(
      'jmp_loop',
      field('target', $.identifier),
    ),

    label_statement: $ => seq(
      $.identifier,
      ':',
    ),

    returnundefined_statement: $ => 'returnundefined',

    return_statement: $ => 'return',

    add_statement: $ => seq(
      'add2',
      field('reserve', $.hexi),
      ',',
      field('register', $.identifier),
    ),

    tonumeric_statement: $ => seq(
      'tonumeric',
      field('reserve', $.hexi),
    ),

    tryldglobalbyname_statement: $ => seq(
      'tryldglobalbyname',
      field('reserve', $.hexi),
      ',',
      '"',
      field('object',$.identifier,),
      '"'
    ),

    inc_statement: $ => seq(
      'inc',
      field('reserve', $.hexi),
    ),
    strictnoteq_statement: $ => seq(
      'strictnoteq',
      field('reserve', $.hexi),
      ',',
      field('register', $.identifier),
    ),

    stricteq_statement: $ => seq(
      'stricteq',
      field('reserve', $.hexi),
      ',',
      field('register', $.identifier),
    ),

    copyrestargs_statement: $ => seq(
      'copyrestargs',
      field('formal_param_pos', $.hexi),
    ),
    
    supercallspread_statement: $ => seq(
      'supercallspread',
      field('reserve', $.hexi),
      ',',
      field('arguments', $.identifier),
    ),

    throwcallwrong_statement: $ => seq(
      'throw.ifsupernotcorrectcall',
      field('reserve', $.hexi),
    ),

    asyncfunctionenter_statement: $ => 'asyncfunctionenter',

    neg_statement: $ => seq(
      'neg',
      field('reserve', $.hexi),
    ),

    asyncfunctionawaituncaught_statement: $ => seq(
      'asyncfunctionawaituncaught',
      field('function_object', $.identifier),
    ),

    suspendgenerator_statement: $ => seq(
      'suspendgenerator',
      field('generator', $.identifier),
    ),

    getresumemode_statement: $ => 'getresumemode',
    
    asyncfunctionresolve_statement: $ => seq(
      'asyncfunctionresolve',
      field('object', $.identifier),
    ),

    asyncfunctionreject_statement: $ => seq(
      'asyncfunctionreject',
      field('object', $.identifier),
    ),

    createemptyarray_statement: $ => seq(
      'createemptyarray',
      field('reserve', $.hexi),
    ),

    createobjectwithbuffer_statement: $ => seq(
      'createobjectwithbuffer',
      field('reserve', $.hexi),
      ',',
      $.literal,
    ),

    createemptyobject_statement: $ => 'createemptyobject',

    isin_statement: $ => seq(
      'isin',
      field('reserve', $.hexi),
      ',',
      field('object', $.identifier),
    ),

    // class_body:$ =>seq(
    //   '{',
    //   field('literal_num',$.deci),
    //   '[',
    //   repeat($.element),
    //   ']',
    //   '}'
    // ),
    method_in_class: $ => seq(
      'string:'
      
    ),

    elements: $ => commaSep1($.element),

    element: $ => seq(
      field(
        'type', 
        choice($.type, 'method', 'method_affiliate')
      ),
      ':',
      choice(
        $.deci,
        $.hexi,
        $.identifier,
        $.string
      ),
      ','
    ),

    literal: $ => seq(
      '{',
      field('length', $.deci),
      '[',
      repeat($.element),
      ']',
      '}'
    ),

    comment: $ => choice(
      $.line_comment,
      $.block_comment,
    ),

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

    line_comment: _ => token(prec(PREC.COMMENT, seq('//', /.*/))),
    
    block_comment: _ => token(prec(PREC.COMMENT,
      seq('/*', /[^*]*\*+([^/*][^*]*\*+)*/, '/')
    )),

    identifier: $ => /[_a-zA-Z][_a-zA-Z0-9]*/,  
    hexi: $ => /0[xX][0-9a-fA-F]+/,
    deci: $ => /[0-9]+/,
  }
  

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

function periodSep1(rule) {
  return sep1(rule, '.');
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

function periodSep(rule) {
  return optional(periodSep1(rule));
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from syntax import SyntaxModule

sm = SyntaxModule()
sent = 'когда будут каникулы?'
print(sm.question_prob(sent))
sent = 'когда будут каникулы?'
print(sm.question_prob(sent))

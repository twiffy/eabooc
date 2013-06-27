// Copyright 2012 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


// When the assessment page loads, activity-generic.js will render the contents
// of the 'assessment' variable into the enclosing HTML webpage.

// For information on modifying this page, see
// https://code.google.com/p/course-builder/wiki/CreateAssessments.


var assessment = {
  // HTML to display at the start of the page
  preamble: '<b>You are only allowed to take this quiz one time.  It has thirty items and each item is worth one half-point.  The 15 points count towards the 100 points possible in this class.<br><br>Directions:  Please read each of the statements presented below, then signify whether the statement is Accurate or Inaccurate.  A statement’s accuracy depends on whether it represents a verbatim or appropriately paraphrased rendition of statements drawn from Chapter 7’s (1) item-writing guidelines for short-answer items, (2) item-writing guidelines for essay items, (3) guidelines for scoring responses to essay items or, from Chapter 6, (4) the five general item-writing commandments.<Br>',

  // An ordered list of questions, with each question's type implicitly determined by the fields it possesses:
  //   choices              - multiple choice question (with exactly one correct answer)
  //   correctAnswerString  - case-insensitive string match
  //   correctAnswerRegex   - freetext regular expression match
  //   correctAnswerNumeric - freetext numeric match
  questionsList: [

    {questionHTML: 'Directions regarding how students should respond to classroom assessments intended to be especially challenging should be somewhat opaque in order to increase the assessment’s difficulty.',
     choices: ['Accurate',
               correct('Inaccurate')],
     // the (optional) lesson associated with this question, which is displayed as a suggestion
     // for further study if the student answers this question incorrectly.
     lesson: '3.1'},
	 

    {questionHTML: 'All student responses to essay tests should be first scored analytically, then scored holistically.',
     choices: ['Accurate',
               correct('Inaccurate')],
     // the (optional) lesson associated with this question, which is displayed as a suggestion
     // for further study if the student answers this question incorrectly.
     lesson: '3.1'},
	 
	    {questionHTML: 'Short-answer items, especially those intended for young children, should employ direct questions rather than incomplete statements.',
     choices: [correct('Accurate'),
               'Inaccurate'],
     // the (optional) lesson associated with this question, which is displayed as a suggestion
     // for further study if the student answers this question incorrectly.
     lesson: '3.1'},	 
	 
    {questionHTML: 'To best assess students’ ability to respond to essay items, allow students to choose among optional items.',
     choices: ['Accurate',
               correct('Inaccurate')],
     // the (optional) lesson associated with this question, which is displayed as a suggestion
     // for further study if the student answers this question incorrectly.
     lesson: '3.1'},	
	 
    {questionHTML: 'Short-answer items, especially those intended for young children, should employ direct questions rather than incomplete statements.',
     choices: [correct('Accurate'),
               'Inaccurate'],
     // the (optional) lesson associated with this question, which is displayed as a suggestion
     // for further study if the student answers this question incorrectly.
     lesson: '3.1'},	 

    {questionHTML: 'When using blanks for short-answer incomplete statements, make sure the blanks for all items are equal in length.',
     choices: [correct('Accurate'),
               'Inaccurate'],
     // the (optional) lesson associated with this question, which is displayed as a suggestion
     // for further study if the student answers this question incorrectly.
     lesson: '3.1'},	  
 

    {questionHTML: 'Construct all essay items so a students task is explicitly described.',
     choices: [correct('Accurate'),
               'Inaccurate'],
     // the (optional) lesson associated with this question, which is displayed as a suggestion
     // for further study if the student answers this question incorrectly.
     lesson: '3.1'},

   
  ],

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'Mid', // unique name submitted along with all of the answers

  checkAnswers: false     // render a "Check your Answers" button to allow students to check answers prior to submitting?
}


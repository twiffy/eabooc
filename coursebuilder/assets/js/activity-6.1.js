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


// Usage instructions: Create a single array variable named 'activity'. This
// represents explanatory text and one or more questions to present to the
// student. Each element in the array should itself be either
//
// -- a string containing a set of complete HTML elements. That is, if the
//    string contains an open HTML tag (such as <form>), it must also have the
//    corresponding close tag (such as </form>). You put the actual question
//    text in a string.
//
// -- a JavaScript object representing the answer information for a question.
//    That is, the object contains properties such as the type of question, a
//    regular expression indicating the correct answer, a string to show in
//    case of either correct or incorrect answers or to show when the student
//    asks for help. For more information on how to specify the object, please
//    see http://code.google.com/p/course-builder/wiki/CreateActivities.

//
// This is not "real" javascript.  The Python code must be able to parse it,
// and gives parse errors (not semantic errors) if you (e.g.) use different
// fields than it expects.
//

var activity = [

  '<p>These self-assessments are mainly intended for you to check your undersanding about the concepts covered on each unit. They do not affect your final grade.</p>',

  '<h1>Unit 6 (Chapter 4) Practice Test</h1>',

  '<h2>Question 1</h2>',

  "<p>What is the chief difference between predictive criterion-related validity evidence and concurrent criterion-related validity evidence?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The key difference is the duration of time between the administration of the predictor test and the collection of the criterion variable.  Concurrent criterion-related evidence of validity, as suggested by its title, is gathered almost immediately.  Predictive criterion-related evidence is gathered after a much longer interval.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"

  },



  '<h2>Question 2</h2>',
  "<p>Why was it suggested in the chapter that “consequential validity,” although a well-intentioned concept, should not be regarded as a legitimate form of validity evidence?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Because the uses or misuses of a test’s results, that is, the 'consequences' of its usage, are not directly relevant to the accuracy of a score-based inference about a student’s status with respect to the curricular aim represented by a test.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


  '<h2>Question 3</h2>',
  "<p>If a classroom test yields results that are quite unreliable, how likely is it that a teacher will be able to arrive at valid score-based inferences about a student’s status?  Why?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Rarely can a teacher make valid interpretations from an unreliable test.  For instance, if a set of stability evidence indicates that students’ scores are bouncing all over when the test is administered on different occasions, it is unlikely that an accurate score-based inference can be based on any given performance by students.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },



  '<h2>Question 4</h2>',
  "<p>How could a classroom test that is “face valid” lead a teacher to make inaccurate inferences about students?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Because a test *appears* to measure the curricular aim it is supposed to represent, this does not necessarily mean the test actually does.  For instance, a test might look like a mathematics test, but turn out to be based more on students’ abilities to *read* the test’s word problems than students’ ability to display the mathematics skills called for in those word problems.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


];


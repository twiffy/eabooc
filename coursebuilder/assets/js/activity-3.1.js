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

  '<table border="2"><tr><td><b>Note:</b><p>These self-assessments are mainly intended for you to check your undersanding about the concepts covered on each unit. They do not affect your final grade.<p></td></tr></table><br>',

  '<table border="2"><tr><td><p><b>Directions:</b> Each of the following statements are inaccurate. Rewrite the statement so that it is accurate.</p></td></tr></table><br>',

  "<h2>Question 1</h2>Inaccurate statement:",
  "<blockquote>To best assess students’ ability to respond to essay items, allow students to choose among optional items.</blockquote>",
  "Your rewrite:<br>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "'To best assess students’ ability to respond to essay items, do not allow students to choose among optional items.'\n\nReasoning: When students have options in which questions to answer, you are allowing them to essentially all take different tests, which limits the inferences you can make about the tests especially when making teaching decisions or comparing students to one another.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 2</h2>Inaccurate statement:",
  '<blockquote>When teachers score their students’ responses to essay questions, teachers should score all of a particular student’s responses to different questions, then move on to scoring the next student’s responses.</blockquote>',
  "Your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "'When teachers score their students’ responses to essay questions, teachers should score all responses to a single question before moving onto score the responses to the next questions.'\n\nReasoning: You should score just one question at a time in order to score the answers consistently from one student to the next.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 3</h2>Inaccurate statement:",
  "<blockquote>For short-answer items employing incomplete statements, use at least two blanks per item, preferably more.</blockquote>",
  "Your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "'For short-answer items employing incomplete statements, use no more than two blanks per item.'\n\nReasoning: Popham calls an item with more than two blanks a “swiss-cheese item” that can cause a great deal of confusion among the test takers. And confusion in test-taking can lead to an inability to make sound inferences regarding the student’s actual learning of the curricular aim.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 4</h2>Inaccurate statement:",
  '<blockquote>Short-answer items, especially those intended for young children, should employ incomplete statements rather than direct questions.</blockquote>',
  "Your rewrite:<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "'Short-answer items, especially those intended for young children, should employ direct questions rather than incomplete statements.'\n\nReasoning: Learners, especially young learners, are more familiar with direct questions and so will be less confused when direct questions are used. Also, a direct question requires the learner to create an answer versus simply write a missing word in a sentence and, thus, the test-item would be more challenging.",
    correctAnswerOutput: "bug"
  },

];


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

  '<table border="2"><tr><td><b>Note:</b><p>These self-assessments are mainly intended for you to check your undersanding about the concepts covered on each unit. They do not affect your final grade.<p></tr></td></table><br>',

  "<h2>Question 1</h2>Consider the following curricular aim: “At the end of the 10-week unit on narrative writing, students will be able to write an acceptable narrative essay on any assigned topic dealing with an historical event with which they are familiar.”  Is this a small-scope curricular aim or a broad-scope curricular aim?<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "A broad-scope curricular aim.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 2</h2>What is the significant difference, if any, between a “curricular aim” and a “content standard?”<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "There is no significant difference.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 3</h2>Is there substantial agreement among educators regarding the concept of “alignment” between curriculum and assessment?  If so, what is the agreed meaning?  If not, why is there disagreement regarding this concept?<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "There is considerable disagreement among educators regarding the meaning of “alignment” largely because of variations in the stringency required for genuine alignment.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 4</h2>Why is it technically inaccurate to refer to a “criterion-referenced test” or a “norm-referenced test?”<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "It is the inference, not the test, that is norm- or criterion-referenced.",
    correctAnswerOutput: "bug"
  },

];


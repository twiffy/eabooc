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

  '<table border="2"><tr><td><p><b>Directions:</b> Each of the following items is based on a flawed selected-response test item.  There will be one <em>dominant</em> deficit in each item.  The deficits will reflect violations either of the chapter’s five general item-writing commandments or of the item-writing guidelines associated with the type of selected-response item presented.  You are to identify each item’s dominant shortcoming in the space provided.</p> <p><b>Note:</b> These items may have additional shortcomings, but the answer key will show you the <em>dominant</em> shortcoming of each item.</p></td></tr></table><br>',

  "<h2>Question 1</h2>Examine the following test item.",
  "<blockquote><u>True or False?</u> A classroom test that <em>validly</em> measures appropriate knowledge and/or skills is likely to be reliable because of the strong link between validity and reliability.</blockquote>",
  "What is this item's dominant shortcoming?<br>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "This is a double-concept item.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 2</h2>Examine the following test item.",
  '<blockquote>Which of the following isn’t an example of how one might collect construct-related evidence of validity?<ol type="A"><li>intervention studies</li><li>test-retest studies</li><li>differential-population studies</li><li>related-measures studies</li></ol></blockquote>',
  "What is this item's dominant shortcoming?<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "This item violates the guideline urging the avoidance of negatives in a multiple-choice item’s stem.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 3</h2>Examine the following test item.",
  "<blockquote><u>Directions:</u> On the line to the left of each state in Column A write the letter of the city from the list in Column B that is the state’s capitol.  Each city in Column B can be used only once.  <table style=\"border-collapse:collapse\"> <tr><th>Column A</th><th>Column B</th></tr> <tr> <td>____ 1. Oregon</td> <td>a. Bismarck</td> </tr> <tr> <td>____ 2. Florida</td> <td>b. Tallahassee</td> </tr> <tr> <td>____&nbsp;3.&nbsp;California</td> <td>c.&nbsp;Los&nbsp;Angeles</td> </tr> <tr> <td>____&nbsp;4.&nbsp;Washington</td> <td>d. Salem</td> </tr> <tr> <td>____ 5. Kansas</td> <td>e. Topeka</td> </tr> <tr> <td></td> <td>f. Sacramento</td> </tr> <tr> <td></td> <td>g. Olympia</td> </tr> <tr> <td></td> <td>h. Seattle</td> </tr> </table> </blockquote>",
  "What is this item's dominant shortcoming?<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The responses are not ordered logically.",
    correctAnswerOutput: "bug"
  },


  "<h2>Question 4</h2>Examine the following test item.",
  '<blockquote> A set of properly constructed binary-choice items will: <ol type="A"><li>Typically contain a substantially greater proportion of items representing one of the two alternatives available to students.</li> <li>Incorporate qualities that permit students to immediately recognize the category into which each item falls, even based on only superficial analyses.</li> <li>Vary the length of items representing each of the two binary-option categories so that, without exception, shorter items represent one category while longer items represent the other.</li> <li>Contain no items in which more than a single concept is incorporated in each of the items.</li> </ol> </blockquote>',
  "What is this item's dominant shortcoming?<br>",
  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "This item’s stem is too terse and its alternatives too verbose.",
    correctAnswerOutput: "bug"
  },

];


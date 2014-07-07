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

  '<h1>Unit 9 (Chapter 14) Practice Test</h1>',

  '<h2>Question 1</h2>',

  "<p>In the district where he teachers, Miles Monroe knows that each spring’s accountability exams consist largely of brand-new items. However, it is necessary to make statistical adjustments in order for one year’s exams to represent the same challenge to students as to all other years’ exams. To do so, however, some “anchor” items must be reused on each form so these statistical adjustments are possible. In all, about 15 percent of each form’s items are reused. Miles has a contact in his district’s office who has told him which of these year’s items will most likely be reused in the next year’s exams. Accordingly, Miles makes copies of those items, then gives his next year’s students plenty of practice with the items prior to their taking the spring exams. After all, John concludes, “There will be 85 percent of the items that my students will never have seen!”</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Miles clearly violates both of the test preparation guidelines. Really, 15 percent cheating is still cheating. If Miles’ conduct were ever divulged to the public, it would reflect negatively on the education profession. In addition to flopping on the professional guideline, Miles also violated the educational defensibility guideline because, with a 15 percent advantage, his students’ spring test scores will surely provide an inflated estimate of students’ actual skills and knowledge.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"

  },



  '<h2>Question 2</h2>',
  "<p>Jennifer Jones is preparing her second-grade students to take end-of-school-year state accountability tests in reading and mathematics. Because this will be the first time these students have ever taken any sort of standardized test, Jennifer believes they will be intimidated by the experience. Accordingly, during the month immediately prior to state testing, Jennifer spends about an hour a week, divided into sessions of about 15 minutes each, showing her students samples of the item types they will be encountering. She has downloaded these items from her State Department of Education’s website.</p>",
  "<p>During these “get-ready” sessions, Jennifer also tells her students how to allocate their test-taking time wisely, and how to make informed guesses when attempting to answer certain kinds of items. Her chief goal in these “get-ready” sessions is to reduce students’ anxiety about the upcoming tests.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Jennifer seemed to be prepping her second-graders sensibly for their upcoming state “first-time” exams. Her focus on anxiety reduction is commendable. Moreover, her test-prep efforts did not last for an eternity. No guideline violations are seen here.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },


  '<h2>Question 3</h2>',
  "<p>Danielle Harris teaches French in an urban high school. For a number of years in a row, students in her school have failed to score well enough on the state’s annual accountability tests in mathematics. Danielle’s principal, at a midyear faculty meeting, pointed out if the school’s students do not do well enough on the upcoming year’s accountability tests, the school is likely to be “restructured.”</p>",
  "<p>In an effort to help her school avoid being restructured, Danielle abandons the teaching of French in her five classes altogether for the six weeks leading up to the accountability testing. Because she is quite skilled in math, Danielle believes she can help her students boost their state math scores sufficiently.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "This seems to be a clear violation of the professional ethics guideline. Danielle is selling out. Her intentions may be commendable, but she’s supposed to be teaching French to her students. If the public ever learns that the teachers are subverting what they’re supposed to be teaching, then it will become apparent the school’s teachers are concerned about what will make their school look good, and not what’s educationally good for their students.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },



  '<h2>Question 4</h2>',
  "<p>Frank Davis wants his seventh-graders to perform well on their spring accountability exams. Based on Frank’s familiarity with the kinds of items included in his state’s Annual Mathematics Appraisals, he makes sure that during the school year, and especially during the twelve weeks immediately prior to the state exams, his students receive highly focused pre-exam preparation, but he uses only the specific type of test items used on the upcoming Annual Mathematics Appraisals.</p>",
  "<p>The state’s math tests for the seventh-graders consists exclusively of “grid-in” items--that is, items for which students supply their answers by bubbling in certain numbers from a numerical grid supplied along with each item. This “grid-in” approach makes it possible to score student’s answers via electronic scanning and thereby permit the state to supply complete reports to each of the state’s teachers within one week after the exams are administered. Because “grid-in” items are not used in the state’s mathematics tests until the seventh-grade, Frank believes his students need all the “gridding-in” practice they can get.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Frank violated the educational defensibility guideline. By providing his students only with practice on “grid-in” items, those students are apt to do all right on the impending statewide exams. But there is life after state accountability exams, and students don’t encounter any “grid-in” items in real life. Come to think of it, when was the last time that you personally had to “grid-in” an answer to a math problem? Frank’s students’ scores on the “grid-in” state tests are likely to be better than those students’ actual math mastery if they had been tested in other ways. Frank needs to vary his practice items. ",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },


];


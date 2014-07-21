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

  '<h1>Unit 11 (Chapter 16) Practice Test</h1>',

  "<p><b>Directions:</b> For each of the following scenarios. provide a critique--negative, positive, or mixed--of the teacher’s actions regarding grading. Frame your critique according to a goal-attainment conception of grading. Keep your responses to one paragraph.</p>",

  '<h2>Question 1</h2>',

  "<p>Daisy Daniels, a high school science teacher, has become a strong proponent of formative assessment in her classes during the past two years. Although she professes a commitment to goal-attainment grading, she invokes this approach only on a small number of grade-determining exams she uses at the conclusion of any extended-duration instructional units (usually lasting at least a month or more). Having already communicated with parents and students about how she will be calculating goal-attainment grades, she then tries to grade each child according to how well that child has mastered the science goals set forth in her classes. However, all of the classroom assessments--both formal and informal--she uses during her regular instruction are never graded. The purpose of these assessments, says Daisy, is “exclusively to help students figure out how to learn what they need to learn.”</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Daisy’s decision not to grade any of her students’ assessments used as part of the formative-assessment process is completely consonant with a goal-attainment conception of grading. If she wishes to use her ongoing assessments to helps students master her curricular goals, then use other exams to verify students’ final levels of goal attainment, this makes instructional sense. Why base students’ grades on the early stages of learning when those students have yet to really master what is being taught? If the function of tests during the formative-assessment process is patently designed to help students learn, not to grade them, then most students will become more willing to “try-and-fail,” because “failing” does not count against them.",
    correctAnswerOutput: "bug",
    outputHeight: "150px"

  },



  '<h2>Question 2</h2>',
  "<p>Lily’s school district has determined that the district students are to be graded according to the degree to which they have mastered the district-specified content standards in each subject. There are many of these content standards, and because Lily teaches fourth graders in multiple subjects, if she used <i>all</i> of the district's content standards, she would be basing a grade on well over 100 goals--clearly, as she says “way too many!“ As a result of this analysis, Lily has decided on the most significant curricular aims (content standards) in each of the subjects she teaches, but never more than six per subject. She sent a note home to parents, and she also informs for students, that even though she will attempt to provide instruction for the full set of more than 100 goals, she will grade students only on their accomplishment of the high-priority goals that she has identified. Given the reduced number of goals, Lily is able to develop clear descriptions of those goals for her students parents, has also created simplified versions of those descriptions for her students. Finally, she supplies students with examples of high-quality and low-quality student responses to illustrate the nature of the goals being sought. These examples are also supplied to any parent who request them.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Lily made a sensible decision, one in line with with the overall intention of a goal attainment grading strategy. In particular, by assuring her students' parents that she will try to give instructional attention to the full array of district sanctioned curricular goals, she makes clear that she will attempt to teach as much of the state approved curriculum as she can, but she will grade her students on the basis of only the high-priority curricular goals.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },


  '<h2>Question 3</h2>',
  "<p>Robert Rogers teachers high school English classes and, after almost a decade of what he now regards as “sloppy grade-giving,” has decided to fully embrace goal-attainment grading. Each year, for every one of his classes, Robert spends a considerable amount of time clarifying the nature of his course curricular goals--and he does this not only for his students, but also for their parents. After the excursion in goal clarification, he chooses the kind of assessment evidence he will use to arrive at an end-of-course estimate of each student’s goal-attainment status. He also decides how much weight to give different sources of evidence when more than one kind of assessment result will be at hand. Robert communicates these decisions to his students and their parents. Finally, he arrives at an overall grade in English for each student based on an amalgam of all the goal-attainment evidence he has assembled As with the other aspects of his grading approach, Robert communicates with parents and students the steps he used to arrive at students’ grades based on the course goals and different students’ mastery of those goals.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Robert appears to be making a sincere effort to carry out the four major operations called for then teachers use a goal-attainment approach to grading: (1) clarifying curricular aims, (2) choosing goal-attainment evidence, (3) weighting the goal-attainment evidence, and (4) arriving at a final goal-attainment grade for each student. Robert appears to be bent on keeping parents actively informed about their students’ grades. From a goal-attainment grading perspective, Robert should be praised.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },



  '<h2>Question 4</h2>',
  "<p>Henry Harrison teaches social studies classes in the suburban, high achieving school. Most of the students in the school come from fairly affluent families, but Henry is continually disappointed in the levels of effort his students seem to be putting into their studies. What he finds particularly vexing is that most of the students, even without expending much visible effort, score really well on Henry's exams as well as on the state accountability test the school students are obliged to take each spring. Accordingly, Henry not only encourages his students to try much harder in their studies but he also devises a “score-plus-effort” grading system. He computes the students’ grade on major exams covering the chief segments of his courses as well as the level-of-effort judgment made by Henry about each student. Because his students recognize the importance of effort expenditure, there are a few complaints from students about this new grading approach.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Although we can appreciate why Henry has become enamored of effort, particularly working with a collection of students who do not seem to be displaying much of it, his approach represents a serious departure from goal-attainment grading. The most serious drawback with Henry's well-intentioned plan is that he cannot accurately estimate each of his students’ individual level of effort. Without being able to do so, his fine-sounding grading approach collapses.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },



];


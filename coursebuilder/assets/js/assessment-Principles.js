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
  preamble: '',

  // An ordered list of questions, with each question's type implicitly determined by the fields it possesses:
  //   choices              - multiple choice question (with exactly one correct answer)
  //   correctAnswerString  - case-insensitive string match
  //   correctAnswerRegex   - freetext regular expression match
  //   correctAnswerNumeric - freetext numeric match
  questionsList: [

    {questionHTML: "A commercial testing company has developed a brand new test intended to measure the mathematics skills of students who possess limited English proficiency.  Because there are three different forms of the test at each of six grade levels, and teachers are encouraged to use all three forms during the year, the sales representatives of the company are demanding reliability evidence (from technical personnel) that will best help them market the new test. What kind of reliability evidence seems most useful in this situation?",
      choices: [
        'Stability',
      correct('Alternate-Forms'),
      'Internal Consistency',
      ],

    },

    {questionHTML: "A school district’s testing office has been directed to construct a basic skills test in language arts that can be taken at any point during an extensive three-month summer session by eighth-grade students who failed an earlier test.  By district policy, the earlier test must be passed before students can enroll in the ninth grade.  The school board’s policy, however, says that the student can choose the occasion (one time per student) when an alternate test is administered.  Critics of the policy fear there will be striking differences in students’ performances depending on when they choose to be tested with the alternate test.  What kind of reliability evidence seems most needed in this setting?",
      choices: [
        correct('Stability'),
      'Alternate-Forms',
      'Internal Consistency',
      ],

    },

    {questionHTML: "A Texas school superintendent in a district near the Mexican border has asked his assessment specialist, Mr. Chavez, to create a brief test that will provide the district’s educators with a general idea of immigrant students’ ability to read English.  Mr. Chavez builds a 20-item test, administered with the use of audiotaped directions in Spanish.  All of the items, however, are written in English.  The test’s overall function is to yield a single estimate of a Spanish-speaking student’s ability to read English.  What kind of reliability evidence would be most informative in this situation?",
      choices: [
        'Stability',
      'Alternate-Forms',
      correct('Internal Consistency'),
        ],

    },

    {questionHTML: "A test-contracting firm has agreed to create a three-part social studies test intended to measure sixth-graders’ knowledge of geography, government, and history.  The test is to be used as a statewide assessment to govern the allocation of staff-development funds for elementary teachers.  Because of limitations in administration time, only 15 items are allowed for each of the three content areas. If the test-development firm wants to know if its three test sub-sections are measuring with suitable consistency what they are supposed to be measuring, what kind of reliability evidence would be best?",
      choices: [
        'Stability',
      'Alternate-Forms',
      correct('Internal Consistency'),
        ],
    },


    {questionHTML: "Based on a new state law, high-school students are going to be permitted to take a basic skills graduation test, administered via a computer, at any time during a three-week test-administration window.  Only one version of the test will be available each year, for the test will be substantially revised the following year.  What kind of reliability evidence seems most needed here for each year’s test?",
      choices: [
        'Stability',
      correct('Alternate-Forms'),
      'Internal Consistency',
        ],
    },


    {questionHTML: "True or False. If an accountability test produces a statistically significant disparate impact between minority and majority students’ performances, it is certain to possess assessment bias.",
      choices: [
        'True', correct('False'),
        ],
    },


    {questionHTML: "True or False. For a test item to be biased, it must offend at least one group of students on the basis of that group-members’ personal characteristics such as race, religion, or gender.",
      choices: [
        'True', correct('False'),
        ],
    },


    {questionHTML: "True or False. Typically, judgment-only approaches to the detection of item bias are employed prior to use of empirical bias-detection techniques.",
      choices: [
        correct('True'), 'False',
        ],
    },


    {questionHTML: "True or False. Assessment accommodations require the creation of a substantially new test, hopefully equated to the original test.",
      choices: [
        'True', correct('False'),
        ],
    },


    {questionHTML: "True or False. If a teacher’s classroom test in mathematics deals with content more likely to be familiar to girls than boys, it is likely the test may be biased.",
      choices: [
        correct('True'), 'False',
        ],
    },

    {questionHTML: "A middle-grade social studies teacher, Ms. Graves, has created a 40-item test covering what she believes is supposed to be taught by middle-grade social studies teachers.  As students conclude their middle-school educations, they must complete (according to district policy) a basic skills test in reading, mathematics, and language arts.  Because the scores for all of the school’s students are available to her, Ms. Graves computes correlation coefficients for her students’ scores on her own social studies test versus each of the three district-required tests.  She finds only moderate correlations between her 40-item social studies test and the other three tests.  Thus, she argues that her test is, sensibly, measuring something other than reading, mathematics, and language arts.",
      choices: [
        'Content-related evidence of validity',
        'Criterion-related evidence of validity',
        correct('Construct-related evidence of validity'),
        'None of the above',
        ],
    },


    {questionHTML: "A high school English teacher, Mrs. Dawson, finds that her state’s Board of Education has adopted a set of curricular outcomes for each subject area and each grade range in grades K-12.  These outcomes are referred to as the state’s adopted “Standards of Learning,” that is, SOLs.  Because Mrs. Dawson believes her mid-semester and semester exams are the most important assessment tools for her to use in determining the quality of her own instruction, she reviews the state’s “essential” SOLs for high school English, then carefully decides how many of those SOLs have not been addressed by at least three items in her combined mid-semester and final exams.  Happily, she discovers that all but four of the state’s “essential” SOLs for high school English have been satisfactorily addressed in her two tests.",
      choices: [
        correct('Content-related evidence of validity'),
        'Criterion-related evidence of validity',
        'Construct-related evidence of validity',
        'None of the above',
        ],
    },


    {questionHTML: "Erlinda Cruz teaches fifth-graders in a school whose staff has emphasized mathematics instruction as part of its school improvement program.  Erlinda has developed an end-of-year mathematics exam that she is confident will identify those students who will succeed or will fail in their middle-school mathematics courses.  To verify this belief, she follows as many of her students as she can (those who attend nearby middle schools) to find out what their grades are in any middle-school mathematics course they take.  After three years of this follow-up effort, she has solid evidence that her fifth-grade mathematics exam does, indeed, help identify those students who, in middle school, will sail through their math courses or, instead, stumble in those courses.",
      choices: [
        'Content-related evidence of validity',
        correct('Criterion-related evidence of validity'),
        'Construct-related evidence of validity',
        'None of the above',
        ],
    },


    {questionHTML: "Martin Meadows spends a considerable amount of time making sure his classroom assessments are as polished as he can make them.  To make certain his tests are yielding a relatively unchanging picture of his students’ achievements, he routinely re-administers certain of his tests a day or two after they were initially administered.  He then correlates each student’s first-time score with that same student’s second-time score.  Because of the care with which Martin devises his tests’ items, the relationship between students’ first and second performances is typically quite strong and positive.",
      choices: [
        'Content-related evidence of validity',
        'Criterion-related evidence of validity',
        'Construct-related evidence of validity',
        correct('None of the above'),
        ],
    },


    {questionHTML: "Floyd Bevins, a fourth grade teacher, wants to make sure his final examination in science adequately represents the five high-priority science objectives he has chosen for his students.  Accordingly, he asks a colleague to review the science examination to make sure there are enough items on the exam to provide a reasonably accurate estimate of the extent to which each fourth-grader has mastered the science objectives.  Floyd’s colleague reported that, while four of the five objectives are adequately measured on the exam, one of the objectives seems to be measured by only one item.  Moreover, as the colleague exclaimed, “and it was a pretty weak item!”",
      choices: [
        correct('Content-related evidence of validity'),
        'Criterion-related evidence of validity',
        'Construct-related evidence of validity',
        'None of the above',
        ],
    },


    {questionHTML: "Formative assessment is best thought of as:",
      choices: [
        'A particular type of test',
        'A procedure to be used only by teachers',
        correct('A process in which assessment-elicited evidence informs adjustment decisions'),
        'A fundamental, non-graded approach to classroom assessment so students can, if necessary, alter their learning tactics.',
        ],
    },


    {questionHTML: "Formative assessment is most similar to which of the following?",
      choices: [
        correct('Assessment <em>for</em> learning'),
        'Assessment <em>of</em> learning',
        'Assessment <em>as</em> learning',
        'Assessment <em>against</em> learning',
        ],
    },


    {questionHTML: "Which one of the following types of tests is most frequently, but mistakenly, pushed by its developers as formative assessments?",
      choices: [
        'Nationally standardized achievement tests',
        correct('Interim assessments'),
        'Statewide annual accountability tests',
        'Tests in the National Assessment of Educational Progress',
        ],
    },


    {questionHTML: "Which of the following is <em>not</em> a likely reason that formative assessment is employed less frequently in our schools than the proponents of formative assessment would prefer?",
      choices: [
        'Misunderstandings by teachers regarding the nature of formative assessment',
        'Teachers’ reluctance to alter their current practices',
        'The prevalence of instructionally insensitive accountability tests',
        correct('The absence of truly definitive evidence that formative assessment improves students’ learning'),
        ],
    },


    {questionHTML: "Of the following options, which one is—by far—the most integral to the implementation of formative assessment in a classroom?",
      choices: [
        'A teacher’s willingness to try new procedures in class',
        correct('Use of assessment-elicited evidence to make adjustments'),
        'Teachers’ willingness to refrain from grading most of their students’ exams',
        'Teachers’ use of a variety of both selected-response and constructed-response items',
        ],
    }],

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'Principles', // unique name submitted along with all of the answers

  checkAnswers: false     // render a "Check your Answers" button to allow students to check answers prior to submitting?
}


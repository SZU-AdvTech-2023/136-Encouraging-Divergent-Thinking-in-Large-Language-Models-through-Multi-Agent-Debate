

<h2 align="center">⚖️ MAD: Multi-Agent Debate</h2>

:fire:This work aims to explore the debating capability of LLMs by proposing the **MAD** framework, which stands for **M**ulti-**A**gents **D**ebate.

>
> "Truth emerges from the clash of adverse ideas."<br>
> "真理越辩越明。"
>

<!-- "Good Luck!" -- wxjiao --->
<!-- "Good Luck!" -- zwhe99 --->
<!-- "Good Luck!" -- xing --->

### Brief Introduction

The cognitive behavior of large language models (LLMs) has garnered significant attention in recent times. For example, **self-reflection**, a concept that usually refers to the process of introspection and examination of a person's own thoughts, has also been demonstrated effective with LLMs in solving challenging NLP tasks.
However, we point out that self-reflection can easily fall into the **degeneration of thoughts (DoT)** issue in the follow scenarios: 
- **Bias and Distorted Perception**: Self-perception can be influenced by biases, preconceived notions, and distorted thinking patterns. If an individual's self-reflection is clouded by such biases or distorted thinking, it can lead to :pensive:_inaccurate conclusions and hinder personal growth_.
- **Rigidity and Resistance to Change**: Self-reflection often involves challenging one's beliefs, assumptions, and behaviors. If an individual is resistant to change or holds rigid beliefs, they may :pensive:_struggle to engage in meaningful self-reflection_ that leads to personal growth.
- **Limited External Feedback**: Self-reflection is primarily an internal process, but external feedback can provide valuable perspectives and insights. Without seeking or considering external feedback, an individual may :pensive:_miss important blind spots or alternative viewpoints that can enrich their self-reflection_.


In this project, we have embarked on a journey to explore the potential of a debating interaction framework among LLMs. 
With **MAD**, the nature of agents being in the state of 'tit for tat' determines that (1) the distorted thinking of one agent can be corrected by the other one :grinning:; (2) the resistance to change of one agent will be complemented by the other one :smile:; and (3) either agent can provide external feedback for each other :laughing:.

Obviously, **MAD** is less likely to have the **DoT** issue and can exploit more potential of LLMs. Experiments show that MAD brings significant and consistent improvements on Counterintuitive QA and Commonsense-MT tasks.

JOIN US on this journey of exploring the interaction and debating capability with LLMs. :rocket::rocket::rocket:



## Run

**Preparation**

  ```shell
  pip3 install -r requirements.txt
  ```
* Set your openai API_KEY in `debate4tran.sh`
* Set your openai API_KEY in `interactive.py`

**Run MAD**

```shell
sh debate4tran.sh 
```

**Run Interactive**

If you just want to have a try, you can try the interactive script on your PC.

```shell
python3 interactive.py
```

Or simply try our demo for translation [here](https://3a3262e6a138888bd4.gradio.live/).








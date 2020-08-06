<p align='center'>
	<img src="https://i.ibb.co/P6HGqnf/receipt.png" width="450" title="Designed by Freepik">
 <br>
 <a href='https://pypi.org/project/receipt-parser/'><img alt="Version" src="https://img.shields.io/pypi/v/receipt-parser?logo=pypi&logoColor=FFE873"></a>
   <a href='https://github.com/slgero/receipt_parser/actions?query=workflow%3Abuild'><img alt="GitHub Workflow Status" src="https://github.com/slgero/receipt_parser/workflows/build/badge.svg"></a>
   <a href='https://github.com/slgero/receipt_parser/actions?query=workflow%3A%22Upload+Python+Package%22'><img alt="Upload Python Package"
src="https://github.com/slgero/receipt_parser/workflows/Upload%20Python%20Package/badge.svg"></a>
   <a href="https://www.codefactor.io/repository/github/slgero/receipt_parser"><img src="https://www.codefactor.io/repository/github/slgero/receipt_parser/badge" alt="CodeFactor" /></a>
  <a href='https://opensource.org/licenses/MIT'><img alt="GitHub" src="https://img.shields.io/github/license/slgero/receipt_parser"></a><br> 
</p>

# Receipt parser🧾
## What is it?
**receipt_parser** - Python библиотека, помогающая распознавать товарную позицию из чеков. Для это задачи есть хороший [сервис](https://receiptnlp.tinkoff.ru/#/) от Тинькофф, однако он не справляется с [грязными данными](https://proverkacheka.com/check/9282000100225162-17705-420231526), как на картинке выше. Изначально была задумка использовать нейронные сети, однако в процессе работы, понял, что на разметку нужно потратить много времени/денег, да и модель, основанная на правилах и словарях, даёт хороший [результат](https://github.com/slgero/receipt_parser/tree/master/receipt_parser/benchmarks).

## Features
* распознавание продукта;
* определение категории товара;
* распознавание брендов;
* перевод англицизмов (`хугарден --> hoegaarden`)🍺


## Where to get it
Исходный код в размещен на [GitHub](https://github.com/slgero/receipt_parser).

Библиотека размещёна на [Python package index](https://pypi.org/project/receipt-parser/):
```bash
pip install receipt-parser
```

## Usage
Для распознавания сейчас доступна только [RuleBased](https://github.com/slgero/receipt_parser/blob/master/receipt_parser/receipt_parser.py#L75) модель.

На вход можно подавать как строку:
```python
from receipt_parser import RuleBased

product_desription = 'Нап.пив.ХУГАР.ГРЕЙПФ.н/ф 0.47л'
rb = RuleBased()
rb.parse(product_desription)
```
 *output*:

|    | name                           | product_norm   | brand_norm   | cat_norm            |
|---:|:-------------------------------|:---------------|:-------------|:--------------------|
|  0 | Нап.пив.ХУГАР.ГРЕЙПФ.н/ф 0.47л | напиток, пиво  | hoegaarden   | Воды, соки, напитки |

Так и `pd.DataFrame` *(колонка с товарной позицией должна называться __name__)*:
```python
from receipt_parser import RuleBased

rb = RuleBased()
rb.parse(df)
```
Также в библиотеке есть два вспомогательных класса:
* Normalizer - для нормализации;
* Finder - для поиска по словарям.

## Future work

 - [ ] Добавить тесты
 - [ ] Дополнить словари и собранные датасеты
 - [ ] Поднять сервис
 - [ ] Перейти на нейронные сети...

## Support the project 🤗
Буду рад, если вы:
* найдёте баги;
* сможете оптимизировать код;
* дополните словари и датасеты;
* поможете с разметкой.

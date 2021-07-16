# Dashboard

## How to run?
```python
python main.py
```

## How is this architecture?
The Dash app has been split throughout multiple files for maintainability,
scalability, readability purposes.

main

    |

    -- settings

    |

    -- fcts

    |

    -- data_loader -- load_data

    |

    -- app

        |

        -- sections -- charts

        |

        -- filters

        |

        -- callbacks

    ,_,      ,_,        _
   (O,O)    (*,*)      (o)>
   (   )    (/ \)     / /)
----"-"------"-"-----//""----

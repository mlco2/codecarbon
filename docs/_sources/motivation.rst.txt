.. _motivation:

Motivation
==========

In recent years, Artificial Intelligence, and more specifically Machine Learning, has become remarkably efficient at performing human-level tasks: recognizing objects and faces in images, driving cars, and playing sophisticated games like chess and Go.

In order to achieve these incredible levels of performance, current approaches leverage vast amounts of data to learn underlying patterns and features. Thus, state-of-the-art Machine Learning models leverage significant amounts of computing power, training on advanced processors for weeks or months, consequently consuming enormous amounts of energy. Depending on the energy grid used during this process, this can entail the emission of large amounts of greenhouse gases such as CO₂. 

With AI models becoming more ubiquitous and deployed across different sectors and industries, AI's environmental impact is also growing. For this reason, it is important to estimate and curtail both the energy used and the emissions produced by training and deploying AI models. This package enables developers to track carbon dioxide (CO₂) emissions across machine learning experiments or other programs. 

This package enables developers to track emissions, measured as kilograms of CO₂-equivalents (CO₂eq) in order to estimate the carbon footprint of their work. For this purpose, we use ``CO₂-equivalents [CO₂eq]``, which is a standardized measure used to express the global warming potential of various greenhouse gases: the amount of CO₂ that would have the equivalent global warming impact. For computing, which emits CO₂ via the electricity it is consuming, carbon emissions are measured in kilograms of CO₂-equivalent per kilowatt-hour. As a matter of fact, electricity is generated as part of the broader electrical grid by combusting fossil fuels for example.


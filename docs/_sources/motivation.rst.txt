.. _motivation:

Motivation
==========

In recent years, Artificial Intelligence and, more specifically, Machine Learning, has become remarkably good at performing human-level tasks: recognizing objects and faces in images, driving cars, and playing sophisticated games like chess and Go.

In order to achieve these incredible levels of performance, current approaches leverage vast amounts of data to learn underlying patterns and features. Thus, state-of-the-art Machine Learning models leverage significant amounts of computing power, training on advanced processors for weeks or months, consequently consuming enormous amounts of energy. Depending on the energy grid used during this process, this can entail the emission of large amounts of greenhouse gases such as CO₂ 

With AI models becoming more ubiquitous and deployed across different sectors and industries, AI's environmental impact is also growing. This is why it is important to estimate and curtail both the energy used and the emissions produced by training and deploying AI models. This package enables developers to track emissions, measured as CO₂eq or CO₂-equivalents, across experiments. 

This package enables developers to track emissions, measured as CO₂eq or CO₂-equivalents, across experiments, in order to estimate the carbon footprint of their work. In order to do this, we use ``CO₂-equivalents [CO₂eq]``, which is a standardized measure used to express the global-warming potential of various greenhouse gases. Computing emits CO₂eq due to the electricity sources being used by the electricity grid that it is connected to -- coal and it is consuming, carbon intensity is measured in in grams of CO₂-equivalent per kilowatt-hour.


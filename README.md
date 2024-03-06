# Statistical-Network-Analysis
In this project, Bluesky, a social media application, is represented as a network which depicts the social interactions on the network.

Data Extraction:
- The file project_data.py contains the code to extract the data from Bluesky API.
- As of now, the file also includes comments that contain ideas for furthering the project

The Network Description:

```latex
\begin{tabular}{ll}
\toprule
Name & BlueSky Network Graph \\
Kind & Directed, unweighted \\
Nodes are & People who posted in a community or feed in Bluesky \\
Links are & People who interacted with the posts(likes,replies,reposts) \\
Considerations & This is an example network or overview of the full network \\
\midrule
Number of nodes & 376 \\
Number of links & 1061 (9 self-loops) \\
--- Bidirectional links & 0.189\% \\
Degree (in/out)\tablefootnote{\label{foot0}Distributions summarized with average [min, max].} & 2.82181 [0, 32] \\
Degree\tablefootnote{\label{foot1}Undirected.}\textsuperscript{,}\textsuperscript{\ref{foot0}} & 5.64362 [0, 93] \\
Clustering & 0.0119 \\
Connected & Disconnected \\
Assortativity (degree) & -0.2998 \\
\midrule
Node metadata & Followers\_count, Following\_count \\
Link metadata & like, reply, repost \\
Date of creation & 3/5/2024 \\
Data generating process & Extracting the data using the BlueSky API \\
Ethics & N/A \\
Funding & None \\
Citation & arXiv:2206.00026 \\
Access & https://docs.bsky.app/docs/get-started \\
\bottomrule
\end{tabular}
% footnotes require tablefootnote package (put \usepackage{tablefootnote} in preamble) ```

- The network is described using a [network card](https://github.com/vgentela/Statistical-Network-Analysis/blob/main/Bsky_network_card.tex)
- Network card is a network descriptor which can be imported from the network-cards library. More on network cards in the [paper](https://arxiv.org/abs/2206.00026)
- This is the link to the [GitHub repository](https://github.com/network-cards/network-cards)
  
The Network itself:
This is the network file in the gml format: [Network](https://github.com/vgentela/Statistical-Network-Analysis/blob/main/graph.gml)

Network drawn usign GEPHI:
This is the network file drawn using GEPHI: ![Gephi network](https://github.com/vgentela/Statistical-Network-Analysis/blob/main/Fullnet.png)

License:
All the contents in this repository are licensed using by the [CC0 1.0 Universal LICENSE](https://github.com/vgentela/Statistical-Network-Analysis/blob/main/LICENSE)

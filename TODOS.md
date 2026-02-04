I want to build a clone of google maps. Specifically, I want to have a way to get directions from one place to another. 
We should support biking, walking, and public transport. 
For now it only needs to work in pittsburgh.

Here's what I imagine the user flow to be like:

The user types in their source and destination. The source can also be from the current location and we should support that. 
The tool should generate a route to go from the source to the destination. 
There should be a map in the background (full screen, like google maps), and the route that is selected should be highlighted on the map in blue. 

First, let's make it work for walking directions.

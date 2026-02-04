# TODO

# DONE
### update 3
- Replaced "Use my location" text button with a crosshair icon inside the From input field
- Added turn-by-turn direction steps below route summary (scrollable list with numbered steps and distances)
- Start and end markers now show labeled popups (using the place names from the input fields)


### update 2
Added biking and public transport direction modes.
- 3 SVG icons (Walk, Bike, Transit) at top of panel for mode switching
- Clicking a mode re-fetches the route automatically if start/end are set
- OSRM profiles: foot (walking), bike (biking), driving (transit approximation)

### update 1
I want to build a clone of google maps. Specifically, I want to have a way to get directions from one place to another. 
We should support biking, walking, and public transport. 
For now it only needs to work in pittsburgh.

Here's what I imagine the user flow to be like:

The user types in their source and destination. The source can also be from the current location and we should support that. 
The tool should generate a route to go from the source to the destination. 
There should be a map in the background (full screen, like google maps), and the route that is selected should be highlighted on the map in blue. 

First, let's make it work for walking directions.

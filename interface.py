from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        # Initialize the database connection
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        # Close the database connection
        self._driver.close()

    def bfs(self, start_name, end_name):
        with self._driver.session() as session:
            # Execute Cypher query to find the shortest path, emulating BFS behavior
            query_result = session.run(
                """
                MATCH (source:Location {name: $start_name}), (destination:Location {name: $end_name})
                MATCH route = shortestPath((source)-[:TRIP*]-(destination))
                RETURN [node in nodes(route) | {name: node.name}] AS path
                """,
                start_name=start_name,
                end_name=end_name
            )

            # Construct and return the path data
            path_data = [{"path": record["path"]} for record in query_result]
            return path_data or [{"path": []}]

    def pagerank(self, max_iterations, weight_property):
        # Creates a graph projection and executes PageRank on it
        with self._driver.session() as session:
            # Drop the existing graph projection, if it exists
            session.run("""
                CALL gds.graph.drop('graphProjection', false)
                YIELD graphName, nodeCount, relationshipCount
            """)

            # Create a new graph projection
            session.run("""
                CALL gds.graph.project(
                    'graphProjection',
                    'Location',
                    'TRIP',
                    {
                        relationshipProperties: ['distance', 'fare']
                    }
                )
            """)

            # Execute PageRank on the graph projection
            result = session.run("""
                CALL gds.pageRank.stream('graphProjection', {
                    maxIterations: $max_iterations,
                    relationshipWeightProperty: $weight_property
                })
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) AS node, score
                ORDER BY score DESC
                RETURN node.name AS name, score
            """, max_iterations=max_iterations, weight_property=weight_property)

            # Collect results and return the top and bottom-ranked nodes
            pagerank_results = list(result)
            return [
                {"name": int(pagerank_results[0]["name"]), "score": pagerank_results[0]["score"]},
                {"name": int(pagerank_results[-1]["name"]), "score": pagerank_results[-1]["score"]}
            ]

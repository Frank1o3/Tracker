import math

def get_vel(x1: int | float, y1: int | float, x2: int | float, y2: int | float, t: float) -> tuple[int, int]:
    """
    Calculate the velocity components in the x and y directions based on two points 
    and a time interval.

    Args:
        x1 (int | float): The x-coordinate of the starting position.
        y1 (int | float): The y-coordinate of the starting position.
        x2 (int | float): The x-coordinate of the current position.
        y2 (int | float): The y-coordinate of the current position.
        t (float): The time interval between the starting and current positions.

    Returns:
        tuple[int, int]: A tuple containing the integer values of velocity in the 
                         x (vx) and y (vy) directions, using floor division.
    """
    vx = math.floor((x2 - x1) / t)
    vy = math.floor((y2 - y1) / t)
    return (vx, vy)

def get_future_position(oldX: int | float, oldY: int | float, CX: int | float, CY: int | float, t: float) -> tuple[int, int]:
    """
    Predict the future position based on the previous and current positions and 
    a time interval, using calculated velocity.

    Args:
        oldX (int | float): The x-coordinate of the previous position.
        oldY (int | float): The y-coordinate of the previous position.
        CX (int | float): The x-coordinate of the current position.
        CY (int | float): The y-coordinate of the current position.
        t (float): The time interval between the previous and current positions.

    Returns:
        tuple[int, int]: A tuple containing the predicted x and y coordinates 
                         (newx, newy) as integers, using ceiling to round up.
    """
    vx, vy = get_vel(oldX, oldY, CX, CY, t)
    # Predict the next position by adding velocity scaled by the time interval
    newx = math.ceil(CX + (vx * t))
    newy = math.ceil(CY + (vy * t))
    return (newx, newy)

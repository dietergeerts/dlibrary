from dlibrary.layer.layer import Layer
from dlibrary.utility.singleton import SingletonMeta
import vs


# class Drawing(object, metaclass=SingletonMeta):
#     @property
#     def area(self, layer: Layer) -> int:
#         p1, p2 = vs.GetDrawingSizeRectN(layer.handle)



# unitPrecision := GetPrefLongInt(162); IF unitprecision > 9 THEN unitPrecision := -1;
# Layer(GetLName(GetLayer(titleBlock)));
# GetDrawingSizeRect(pointA.X, pointA.Y, pointB.X, pointB.Y);
# areaFieldValue := Num2Str(unitPrecision,
#                           (((((pointB.X - pointA.X) * (pointA.Y - pointB.Y)) / 100) / GetPrefReal(152)) * (100 / GetPrefReal(152))) * GetPrefReal(176));
# SetRField(titleBlock, recordName, areaFieldName, areaFieldValue);

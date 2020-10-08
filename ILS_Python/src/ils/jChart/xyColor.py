'''
Code to be used in the configureChart extension function
for a jfreechart xy scatter plot

@author: phass
'''
import system
import org.jfree.chart.renderer.xy.AbstractXYItemRenderer as AbstractXYItemRenderer
import java.awt.Color as Color
import java.awt.geom.Rectangle2D as Rectangle2D
import org.jfree.chart.plot.PlotOrientation as PlotOrientation
import org.jfree.util.ShapeUtilities as ShapeUtilities
from ils.jChart.common import getPlot
log = system.util.getLogger("com.ils.jChart.xyColor")

# Configure the chart with a custom renderer that colors
# the points based on their place within the sequence.
# c1 and c2 are the starting and ending colors.
def configure(chart, jChart, c1, c2, datasetIndex):
    log.infof("In %s.configure: dataset index: %d, color: (%d,%d,%d)->(%d,%d,%d)", __name__, datasetIndex, c1.getRed(), c1.getGreen(), c1.getBlue(), c2.getRed(), c2.getGreen(), c2.getBlue())
    renderer = colorRenderer(c1,c2)
    plot = getPlot(jChart,0)
    plot.setRenderer(datasetIndex,renderer)

 
# Render scatterplot points with different colors for each
# point pased on its age - actually position in array.
class colorRenderer (AbstractXYItemRenderer):
     
    def __init__(self,c1,c2):
        log.tracef("Initializing a new renderer!")
        self.c1 = c1
        self.c2 = c2
        log.tracef("start color: (%d, %d, %d, %d)", c1.getRed(), c1.getGreen(), c1.getBlue(), c1.getAlpha())
        log.tracef("end color: (%d, %d, %d, %d)", c2.getRed(), c2.getGreen(), c2.getBlue(), c2.getAlpha())
        
        
    # Overrite
    def drawItem(self,g2, state, dataArea, info, plot, domainAxis, rangeAxis, dataset,  series, item, crosshairState, success):
        shape = self.getItemShape(series,item)
        #shape =  Rectangle2D.Double(-5., -5., 10., 10.)
        
        x = dataset.getXValue(series, item)
        y = dataset.getYValue(series, item)
        transX = domainAxis.valueToJava2D(x, dataArea,plot.getDomainAxisEdge())
        transY = rangeAxis.valueToJava2D(y, dataArea,plot.getRangeAxisEdge())
        orientation = plot.getOrientation();
        if orientation == PlotOrientation.HORIZONTAL:
            shape = ShapeUtilities.createTranslatedShape(shape, transY,transX)
        elif orientation == PlotOrientation.VERTICAL:
            shape = ShapeUtilities.createTranslatedShape(shape, transX,transY)
        
#        count = plot.getDataset().getItemCount(series) - 1
        count = dataset.getItemCount(series) - 1
        if count<1: count = 1
        log.tracef("drawItem: (%f, %f) - %d of %d", x, y, int(item),int(count))
        
        color = self.interpolate(self.c1,self.c2, float(item)/count)
        log.tracef("   using interpolated color: (%d,%d,%d)", int(color.getRed()), int(color.getGreen()), int(color.getBlue()))
        g2.setPaint(color)
        g2.fill(shape)
        g2.draw(shape)
        

    # frac is (0.,1.]
    def interpolate(self,c1,c2,frac):
        red   = c1.getRed()*frac   + c2.getRed()*(1.-frac)
        green = c1.getGreen()*frac + c2.getGreen()*(1.-frac)
        blue  = c1.getBlue()*frac  + c2.getBlue()*(1.-frac)
        alpha = c1.getAlpha()*frac + c2.getAlpha()*(1.-frac)
        
        # Args are float values in the range (0,1)
        return Color(red/255., green/255., blue/255., alpha/255.)      
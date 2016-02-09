package org.distributedsearch.node;

import javax.xml.bind.annotation.*;


@XmlRootElement(name="resultItem")
@XmlAccessorType(XmlAccessType.FIELD)
public class ResultItem {
	@XmlElement(name = "description")
	public String description;
	@XmlElement(name = "category")
	public String category;
	@XmlElement(name = "location")
	public String location;
}

package org.distributedsearch.node;

import javax.xml.bind.annotation.*;


@XmlRootElement(name = "search")
@XmlAccessorType(XmlAccessType.FIELD)
public class Search {
	@XmlElementWrapper(name = "categories")
	@XmlElement(name = "category")
	public String[] categories;
	@XmlElement(name = "q")
	public String q;
}
